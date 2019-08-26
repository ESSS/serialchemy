import datetime

import pytest

from serialchemy._tests.sample_model import Address, Company, Department, Employee, Manager, Engineer
from serialchemy.field import Field
from serialchemy.func import dump
from serialchemy.nested_fields import NestedAttributesField, NestedModelField, PrimaryKeyField
from serialchemy.model_serializer import ModelSerializer
from serialchemy.polymorphic_serializer import PolymorphicModelSerializer


class EmployeeSerializerNestedModelFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedModelField(Address)
    company = NestedModelField(Company)


class EmployeeSerializerNestedAttrsFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedAttributesField(('id', 'street', 'number', 'city'))
    company = NestedAttributesField(('name', 'location'))
    department = NestedAttributesField(('name',))


class EmployeeSerializerPrimaryKeyFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = PrimaryKeyField(Address)
    company = PrimaryKeyField(Company)
    department = PrimaryKeyField(Department)


class EmployeeSerializerMixedFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedAttributesField({'id': int, 'street': str, 'number': str, 'city': str})
    company = NestedModelField(Company)
    department = PrimaryKeyField(Department)


class EmployeeSerializerHybridProperty(ModelSerializer):

    full_name = Field(dump_only=True)


class EmployeeSerializerProtectedField(ModelSerializer):

    _role = Field()


class EmployeeInheritedModelSerializer(PolymorphicModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)


class CompanySerializer(ModelSerializer):

    employees = PrimaryKeyField(Employee)


class EmployeeSerializerCreationOnlyField(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    email = Field(creation_only=True)


@pytest.fixture(autouse=True)
def seed_data(db_session):
    company = Company(id=5, name='Terrans', location='Korhal')
    emp1 = Manager(id=1, firstname='Jim', lastname='Raynor', role='Manager', _salary=400, company=company)
    emp2 = Engineer(id=2, firstname='Sarah', lastname='Kerrigan', role='Engineer', company=company)
    emp3 = Employee(id=3, firstname='Tychus', lastname='Findlay')

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1
    emp2.address = addr1

    db_session.add_all([company, emp1, emp2, emp3])
    db_session.commit()


def test_model_dump(db_session, data_regression):
    emp = db_session.query(Employee).get(1)
    serializer = ModelSerializer(Employee)
    serialized = serializer.dump(emp)
    data_regression.Check(serialized)


def test_model_load(data_regression):
    serializer = ModelSerializer(Employee)
    employee_dict = {
        "firstname": "Sarah",
        "lastname": "Kerrigan",
        "email": "sarahk@blitz.com",
        "admission": "2152-01-02T00:00:00"
    }
    model = serializer.load(employee_dict)
    data_regression.Check(dump(model))


@pytest.mark.parametrize("serializer_class",
    [EmployeeSerializerNestedModelFields, EmployeeSerializerNestedAttrsFields]
)
def test_custom_serializer(serializer_class, db_session, data_regression):
    emp = db_session.query(Employee).get(1)
    serializer = serializer_class(Employee)
    serialized = serializer.dump(emp)
    data_regression.check(serialized, basename="test_custom_serializer_{}".format(serializer_class.__name__))


def test_deserialize_with_custom_serializer(db_session, data_regression):
    serializer = EmployeeSerializerNestedModelFields(Employee)
    serialized = {
        "firstname": "John",
        "lastname": "Doe",
        "company_id": 5,
        "admission": "2004-06-01T00:00:00",
        "address": {
            "number": "245",
            "street": "6 Av",
            "zip": "88088-000"
        },
        # Dump only field, must be ignored
        "created_at": "2023-12-21T00:00:00",
    }
    loaded_emp = serializer.load(serialized, session=db_session)
    data_regression.check(serializer.dump(loaded_emp))


def test_deserialize_existing_model(db_session):
    original = db_session.query(Employee).get(1)
    assert original.firstname == "Jim"
    assert original.address.zip is None

    serializer = EmployeeSerializerNestedModelFields(Employee)
    serialized = {
        "id": 1,
        "firstname": "James Eugene",
        "address": {
            "zip": "88088-000"
        },
    }

    loaded_emp = serializer.load(serialized, session=db_session)
    assert serialized["id"] == loaded_emp.id
    assert serialized["firstname"] == loaded_emp.firstname
    assert serialized["address"]["zip"] == loaded_emp.address.zip


def test_one2one_pk_field(db_session, data_regression):
    serializer = EmployeeSerializerPrimaryKeyFields(Employee)
    employee = db_session.query(Employee).get(2)
    serialized = serializer.dump(employee)
    data_regression.check(serialized)


def test_one2many_pk_field(db_session, data_regression):
    serializer = CompanySerializer(Company)
    company = db_session.query(Company).get(5)
    serialized = serializer.dump(company)
    data_regression.check(serialized)

    serialized['employees'] = [2, 3]
    company = serializer.load(serialized, existing_model=company, session=db_session)
    assert company.employees[0] == db_session.query(Employee).get(2)
    assert company.employees[1] == db_session.query(Employee).get(3)


def test_empty_nested(db_session):
    serializer = EmployeeSerializerNestedModelFields(Employee)
    serialized = serializer.dump(db_session.query(Employee).get(3))
    assert serialized['company'] is None
    model = serializer.load(serialized, session=db_session)
    assert model.company is None

def test_property_serialization(db_session):
    serializer = EmployeeSerializerHybridProperty(Employee)
    serialized = serializer.dump(db_session.query(Employee).get(2))
    assert serialized['full_name'] is not None


def test_protected_field_default_creation(db_session):

    serializer = EmployeeSerializerProtectedField(Employee)
    employee = db_session.query(Employee).get(1)
    assert employee._salary == 400
    serialized = serializer.dump(employee)
    assert serialized.get('role') == 'Manager'
    assert serialized.get('_salary') is None

    model = serializer.load(serialized, session=db_session)
    assert model.role == 'Manager'
    assert model._salary is None


def test_inherited_model_serialization(db_session):

    serializer = PolymorphicModelSerializer(Employee)

    manager = db_session.query(Employee).get(1)
    assert isinstance(manager, Manager)

    serialized = serializer.dump(manager)
    assert serialized.get('role') == 'Manager'
    model = serializer.load(serialized, session=db_session)
    assert hasattr(model, 'manager_name')

    engineer = db_session.query(Employee).get(2)
    assert isinstance(engineer, Engineer)

    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Engineer'
    model = serializer.load(serialized, session=db_session)
    assert hasattr(model, 'engineer_name')


def test_creation_only_flag(db_session):

    serializer = EmployeeSerializerCreationOnlyField(Employee)

    serialized = {
        "password": "some",
        "email": "spoc@cap.co",
        "firstname": "Spock"
    }

    employee: Employee = serializer.load(serialized)
    db_session.add(employee)
    db_session.commit()

    assert employee.id is not None
    assert employee.email == 'spoc@cap.co'
    assert employee.firstname == 'Spock'

    serialized = {
        "password": "some",
        "email": "other_spoc@cap.co",
        "firstname": "Other Spock"
    }

    changed_employee: Employee = serializer.load(serialized, existing_model=employee)

    assert changed_employee.email == 'spoc@cap.co'
    assert employee.firstname == 'Other Spock'

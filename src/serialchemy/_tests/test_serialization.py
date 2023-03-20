import pytest

from serialchemy._tests.sample_model import (
    Address, Company, ContractType, Department, Employee, Engineer, Manager, MaritalStatus,
    SpecialistEngineer)
from serialchemy.field import Field
from serialchemy.func import dump
from serialchemy.model_serializer import ModelSerializer
from serialchemy.nested_fields import NestedAttributesField, NestedModelField, PrimaryKeyField
from serialchemy.polymorphic_serializer import PolymorphicModelSerializer


class EmployeeSerializerPrimaryKeyFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = PrimaryKeyField(Address)
    company = PrimaryKeyField(Company)
    departments = PrimaryKeyField(Department)


class EmployeeSerializerMixedFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedAttributesField({'id': int, 'street': str, 'number': str, 'city': str})
    company = NestedModelField(Company)
    department = PrimaryKeyField(Department)


class EmployeeSerializerHybridProperty(ModelSerializer):

    full_name = Field(dump_only=True)


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
    emp1 = Manager(
        id=1, firstname='Jim', lastname='Raynor', role='Manager', _salary=400, company=company, marital_status=MaritalStatus.MARRIED
    )
    emp2 = Engineer(id=2, firstname='Sarah', lastname='Kerrigan', role='Engineer', company=company, marital_status=MaritalStatus.MARRIED)
    emp3 = Employee(
        id=3, firstname='Tychus', lastname='Findlay', contract_type=ContractType.CONTRACTOR, marital_status=MaritalStatus.SINGLE
    )
    emp4 = SpecialistEngineer(
        id=4, firstname='Doran', lastname='Routhe', specialization='Mechanical'
    )

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1
    emp2.address = addr1

    db_session.add_all([company, emp1, emp2, emp3, emp4])
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
        "admission": "2152-01-02T00:00:00",
        "marital_status": "Married"
    }
    model = serializer.load(employee_dict)
    data_regression.Check(dump(model))


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


def test_property_serialization(db_session):
    serializer = EmployeeSerializerHybridProperty(Employee)
    serialized = serializer.dump(db_session.query(Employee).get(2))
    assert serialized['full_name'] is not None


def test_protected_field_default_creation(db_session):
    serializer = ModelSerializer(Employee)
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

    engineer = db_session.query(Employee).get(4)
    assert isinstance(engineer, SpecialistEngineer)

    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Specialist Engineer'
    model = serializer.load(serialized, session=db_session)
    assert hasattr(model, 'specialization')


def test_nested_inherited_model_serialization(db_session):

    serializer = PolymorphicModelSerializer(Engineer)

    engineer = db_session.query(Employee).get(2)
    assert isinstance(engineer, Engineer)
    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Engineer'
    assert 'specialization' not in serialized.keys()

    specialist_engineer = db_session.query(Employee).get(4)
    assert isinstance(specialist_engineer, SpecialistEngineer)
    serialized = serializer.dump(specialist_engineer)
    assert serialized.get('role') == 'Specialist Engineer'
    assert 'specialization' in serialized.keys()
    assert serialized.get('specialization') == 'Mechanical'


def test_creation_only_flag(db_session):
    serializer = EmployeeSerializerCreationOnlyField(Employee)

    serialized = {"password": "some", "email": "spoc@cap.co", "firstname": "Spock"}

    employee: Employee = serializer.load(serialized)
    db_session.add(employee)
    db_session.commit()

    assert employee.id is not None
    assert employee.email == 'spoc@cap.co'
    assert employee.firstname == 'Spock'

    serialized = {"password": "some", "email": "other_spoc@cap.co", "firstname": "Other Spock"}

    changed_employee: Employee = serializer.load(serialized, existing_model=employee)

    assert changed_employee.email == 'spoc@cap.co'
    assert employee.firstname == 'Other Spock'


def test_dump_choice_type(db_session, data_regression):
    tychus: Employee = db_session.query(Employee).get(3)
    serializer = ModelSerializer(Employee)
    dump = serializer.dump(tychus)
    data_regression.check(dump)


def test_load_choice_type(db_session):
    json = {
        "password": "some",
        "email": "other_spoc@cap.co",
        "firstname": "Other Spock",
        "contract_type": "Other",
    }

    serializer = ModelSerializer(Employee)
    loaded = serializer.load(json)
    db_session.add(loaded)
    db_session.commit()

    assert loaded.contract_type == ContractType.OTHER

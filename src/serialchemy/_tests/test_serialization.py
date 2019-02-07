import datetime

import pytest

from serialchemy._tests.sample_model import Address, Company, Department, Employee
from serialchemy.fields import Field, NestedAttributesField, NestedModelField, PrimaryKeyField
from serialchemy.modelserializer import ModelSerializer


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


class CompanySerializer(ModelSerializer):

    employees = PrimaryKeyField(Employee)


@pytest.fixture(autouse=True)
def seed_data(db_session):
    company = Company(id=5, name='Terrans', location='Korhal')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)
    emp3 = Employee(id=3, firstname='Tychus', lastname='Findlay')

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1
    emp2.address = addr1

    db_session.add_all([company, emp1, emp2, emp3])
    db_session.commit()


@pytest.mark.parametrize("serializer_class",
    [EmployeeSerializerNestedModelFields, EmployeeSerializerNestedAttrsFields]
)
def test_serialization(serializer_class, db_session):
    emp = db_session.query(Employee).get(1)
    serializer = serializer_class(Employee)
    serialized_dict = serializer.dump(emp)
    assert serialized_dict["firstname"] == emp.firstname
    assert serialized_dict["lastname"] == emp.lastname
    assert serialized_dict["created_at"] == "2000-01-02T00:00:00"
    assert serialized_dict["company_id"] == 5
    assert serialized_dict["company"]["name"] == "Terrans"
    assert serialized_dict["company"]["location"] == "Korhal"

    assert "password" not in serialized_dict
    address = serialized_dict["address"]

    assert address["id"] == 1
    assert address["number"] == "943"
    assert address["street"] == "5 Av"


def test_deserialize_new_model(db_session):
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
    assert loaded_emp.firstname == serialized["firstname"]
    assert loaded_emp.admission == datetime.datetime(2004, 6, 1, 0, 0)
    assert loaded_emp.company_id == serialized["company_id"]
    assert loaded_emp.address.number == "245"
    assert loaded_emp.created_at is None


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


def test_one2one_pk_field(db_session):
    serializer = EmployeeSerializerPrimaryKeyFields(Employee)
    employee = db_session.query(Employee).get(2)
    serialized = serializer.dump(employee)
    assert serialized['firstname'] == 'Sarah'
    assert serialized['address'] == 1
    assert serialized['company'] == 5


def test_one2many_pk_field(db_session):
    serializer = CompanySerializer(Company)
    company = db_session.query(Company).get(5)
    serialized = serializer.dump(company)
    assert serialized['name'] == 'Terrans'
    assert len(serialized['employees']) == 2
    assert serialized['employees'] == [1, 2]

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

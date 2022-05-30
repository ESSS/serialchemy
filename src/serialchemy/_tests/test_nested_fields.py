import pytest

from serialchemy import ModelSerializer
from serialchemy._tests.sample_model import Address, Company, Employee, Manager, Engineer, \
    SpecialistEngineer
from serialchemy.field import Field
from serialchemy.nested_fields import NestedAttributesField, NestedModelField


class EmployeeSerializerNestedModelFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedModelField(Address)
    company = NestedModelField(Company)


class EmployeeSerializerNestedAttrsFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedAttributesField(("id", "street", "number", "city"))
    company = NestedAttributesField(("name", "location"))


@pytest.fixture(autouse=True)
def setup(db_session):
    company = Company(id=5, name='Terrans', location='Korhal')
    emp1 = Manager(id=1, firstname='Jim', lastname='Raynor', role='Manager', _salary=400, company=company)
    emp2 = Engineer(id=2, firstname='Sarah', lastname='Kerrigan', role='Engineer', company=company)
    emp3 = Employee(id=3, firstname='Tychus', lastname='Findlay')
    emp4 = SpecialistEngineer(id=4, firstname='Doran', lastname='Routhe', specialization='Mechanical')

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1
    emp2.address = addr1

    db_session.add_all([company, emp1, emp2, emp3, emp4])
    db_session.commit()


@pytest.mark.parametrize(
    "serializer_class",
    [EmployeeSerializerNestedModelFields, EmployeeSerializerNestedAttrsFields],
)
def test_custom_serializer(serializer_class, db_session, data_regression):
    emp = db_session.query(Employee).get(1)
    serializer = serializer_class(Employee)
    serialized = serializer.dump(emp)
    data_regression.check(
        serialized,
        basename="test_custom_serializer_{}".format(serializer_class.__name__),
    )


def test_deserialize_with_custom_serializer(db_session, data_regression):
    serializer = EmployeeSerializerNestedModelFields(Employee)
    serialized = {
        "firstname": "John",
        "lastname": "Doe",
        "company_id": 5,
        "admission": "2004-06-01T00:00:00",
        "address": {"id": 1, "number": "245", "street": "6 Av", "zip": "88088-000"},
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
        "address": {"zip": "88088-000"},
    }

    loaded_emp = serializer.load(serialized, session=db_session)
    assert serialized["id"] == loaded_emp.id
    assert serialized["firstname"] == loaded_emp.firstname
    assert serialized["address"]["zip"] == loaded_emp.address.zip


def test_empty_nested(db_session):
    serializer = EmployeeSerializerNestedModelFields(Employee)
    serialized = serializer.dump(db_session.query(Employee).get(3))
    assert serialized["company"] is None
    model = serializer.load(serialized, session=db_session)
    assert model.company is None

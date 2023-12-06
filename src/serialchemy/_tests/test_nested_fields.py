import pytest
from freezegun import freeze_time

from serialchemy import ModelSerializer
from serialchemy.field import Field
from serialchemy.nested_fields import NestedAttributesField
from serialchemy.nested_fields import NestedModelField


def getEmployeeSerializerNestedModelFields(model):
    class EmployeeSerializerNestedModelFields(ModelSerializer):

        password = Field(load_only=True)
        created_at = Field(dump_only=True)
        address = NestedModelField(model.Address)
        company = NestedModelField(model.Company)

    return EmployeeSerializerNestedModelFields


class EmployeeSerializerNestedAttrsFields(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedAttributesField(("id", "street", "number", "city"))
    company = NestedAttributesField(("name", "location"))


def getCompanySerializer(model):
    class CompanySerializer(ModelSerializer):

        master_engeneer = NestedModelField(model.SpecialistEngineer)
        master_manager = NestedModelField(model.Manager)

    return CompanySerializer


@pytest.fixture(autouse=True)
def setup(model, db_session):
    company = model.Company(id=5, name='Terrans', location='Korhal')
    emp1 = model.Manager(
        id=1,
        firstname='Jim',
        lastname='Raynor',
        email='some@email.com',
        password='somepass',
        role='Manager',
        _salary=400,
        company=company,
        marital_status=model.MaritalStatus.MARRIED,
    )
    emp2 = model.Engineer(
        id=2,
        firstname='Sarah',
        lastname='Kerrigan',
        email='some@email.com',
        password='somepass',
        role='Engineer',
        company=company,
    )
    emp3 = model.Employee(
        id=3,
        firstname='Tychus',
        lastname='Findlay',
        email='some@email.com',
        password='somepass',
        role='Employee',
    )
    emp4 = model.SpecialistEngineer(
        id=4,
        firstname='Doran',
        lastname='Routhe',
        specialization='Mechanical',
        email='some@email.com',
        password='somepass',
        role='Specialist Engineer',
        marital_status=model.MaritalStatus.MARRIED,
    )

    addr1 = model.Address(street="5 Av", number="943", city="Tarsonis", state='Mich')
    emp1.address = addr1
    emp2.address = addr1

    db_session.add_all([company, emp1, emp2, emp3, emp4])
    db_session.commit()

    company.master_engeneer = emp4
    company.master_manager = emp1
    db_session.commit()


@pytest.mark.parametrize(
    "serializer_strategy",
    ["NestedModelFields", "NestedAttrsFields"],
)
def test_custom_serializer(model, serializer_strategy, db_session, data_regression):
    serializer_class = (
        getEmployeeSerializerNestedModelFields(model)
        if serializer_strategy == "NestedModelFields"
        else EmployeeSerializerNestedAttrsFields
    )
    emp = db_session.query(model.Employee).get(1)
    serializer = serializer_class(model.Employee)
    serialized = serializer.dump(emp)
    data_regression.check(
        serialized,
        basename="test_custom_serializer_{}".format(serializer_class.__name__),
    )


def test_deserialize_with_custom_serializer(model, db_session, data_regression):
    serializer = getEmployeeSerializerNestedModelFields(model)(model.Employee)
    serialized = {
        "firstname": "John",
        "lastname": "Doe",
        "marital_status": "Married",
        "email": "some@email.com",
        "role": "Employee",
        "company_id": 5,
        "admission": "2004-06-01T00:00:00",
        "address": {"id": 1, "number": "245", "street": "6 Av", "zip": "88088-000"},
        # Dump only field, must be ignored
        "created_at": "2023-12-21T00:00:00",
    }
    loaded_emp = serializer.load(serialized, session=db_session)
    data_regression.check(serializer.dump(loaded_emp))


def test_deserialize_existing_model(model, db_session):
    original = db_session.query(model.Employee).get(1)
    assert original.firstname == "Jim"
    assert original.address.zip is None

    serializer = getEmployeeSerializerNestedModelFields(model)(model.Employee)
    serialized = {
        "id": 1,
        "firstname": "James",
        "lastname": "Eugene",
        "email": "some@email.com",
        "password": "somepass",
        "role": "Employee",
        "address": {
            "zip": "88088-000",
            "street": "st. 23",
            "number": 23,
            "city": "Columbia",
            "state": "SC",
        },
    }

    loaded_emp = serializer.load(serialized, session=db_session)
    assert serialized["id"] == loaded_emp.id
    assert serialized["firstname"] == loaded_emp.firstname
    assert serialized["address"]["zip"] == loaded_emp.address.zip


def test_empty_nested(model, db_session):
    serializer = getEmployeeSerializerNestedModelFields(model)(model.Employee)
    serialized = serializer.dump(db_session.query(model.Employee).get(3))
    assert serialized["company"] is None
    model = serializer.load(serialized, session=db_session)
    assert model.company is None


def test_dump_with_nested_polymorphic(model, db_session, data_regression):
    serializer = getCompanySerializer(model)(model.Company)
    serialized = serializer.dump(db_session.query(model.Company).first())
    data_regression.check(serialized)


@freeze_time("2021-06-15")
def test_load_with_nested_polymorphic_with_different_table_pk_names(
    model, db_session, data_regression
):
    # SpecializedEngeneer and its base class Engeneer have different names for the primary key on the database table
    serializer = getCompanySerializer(model)(model.Company)
    serialized = {
        'id': 5,
        'master_engeneer': {'id': 4},
        'name': 'Company 1',
        'location': 'Delawere',
    }
    model = serializer.load(serialized, session=db_session)
    data_regression.check(serializer.dump(model))


def test_load_with_nested_polymorphic_same_table_pk_names(model, db_session, data_regression):
    # Manager and its base class Empoyee have the same name for the primary key on the database table
    serializer = getCompanySerializer(model)(model.Company)
    serialized = {
        'id': 5,
        'master_manager': {'id': 1},
        'name': 'Company 1',
        'location': 'Delawere',
    }
    entity = serializer.load(serialized, session=db_session)
    data_regression.check(
        serializer.dump(entity), basename='test_load_with_nested_polymorphic_same_table_pk_names'
    )

from serialchemy.enum_field import EnumKeyField
from serialchemy.field import Field
from serialchemy.func import dump
from serialchemy.model_serializer import ModelSerializer
from serialchemy.nested_fields import NestedModelField
from serialchemy.nested_fields import NestedModelListField
from serialchemy.nested_fields import PrimaryKeyField
from serialchemy.polymorphic_serializer import PolymorphicModelSerializer


def seed_data(session, model):

    company = model.Company(id=5, name='Terrans', location='Korhal')
    addr1 = model.Address(street="5 Av", number="943", city="Tarsonis", state='NA')
    emp1 = model.Manager(
        id=1,
        firstname='Jim',
        lastname='Raynor',
        role='Manager',
        _salary=400,
        company=company,
        email='some',
        address=addr1,
        password='mypass',
        contract_type=model.ContractType.CONTRACTOR,
        marital_status=model.MaritalStatus.MARRIED,
    )
    emp2 = model.Engineer(
        id=2,
        firstname='Sarah',
        lastname='Kerrigan',
        role='Engineer',
        company=company,
        email='some',
        address=addr1,
        _salary=21.12,
        password='mypass',
        contract_type=model.ContractType.OTHER,
        marital_status=model.MaritalStatus.MARRIED,
    )
    emp3 = model.Employee(
        id=3,
        firstname='Tychus',
        lastname='Findlay',
        email='some',
        company=company,
        address=addr1,
        role='Employee',
        _salary=21.12,
        password='mypass',
        contract_type=model.ContractType.EMPLOYEE,
        marital_status=model.MaritalStatus.SINGLE,
    )
    emp4 = model.SpecialistEngineer(
        id=4,
        firstname='Doran',
        lastname='Routhe',
        specialization='Mechanical',
        role='Specialist Engineer',
        company=company,
        email='some',
        address=addr1,
        _salary=21.12,
        password='mypass',
        contract_type=model.ContractType.OTHER,
    )

    session.add_all([company, emp1, emp2, emp3, emp4])
    session.commit()


def getEmployeeSerializer(model):
    class EmployeeSerializer(ModelSerializer):

        password = Field(load_only=True)
        created_at = Field(dump_only=True)
        company_name = Field(dump_only=True)
        address = NestedModelField(model.Address)
        contacts = NestedModelListField(model.Contact)
        marital_status = EnumKeyField(model.MaritalStatus)

    return EmployeeSerializer


def test_model_dump(model, db_session, data_regression):
    seed_data(db_session, model)

    emp = db_session.query(model.Employee).get(1)
    serializer = ModelSerializer(model.Employee)
    serialized = serializer.dump(emp)
    data_regression.check(serialized, basename='test_model_dump')


def test_enum_key_field_dump(model, db_session, data_regression):
    seed_data(db_session, model)

    emp = db_session.query(model.Employee).get(1)
    serializer = getEmployeeSerializer(model)(model.Employee)
    serialized = serializer.dump(emp)
    data_regression.check(serialized, basename='test_enum_key_field_dump')


def test_model_load(model, data_regression):
    serializer = ModelSerializer(model.Employee)
    employee_dict = {
        "firstname": "Sarah",
        "lastname": "Kerrigan",
        "email": "sarahk@blitz.com",
        "admission": "2152-01-02T00:00:00",
        "marital_status": "Married",
        "role": "Employee",
    }
    model = serializer.load(employee_dict)
    data_regression.check(dump(model))


def test_enum_key_field_load(model, data_regression):

    serializer = getEmployeeSerializer(model)(model.Employee)
    employee_dict = {
        "firstname": "Sarah",
        "lastname": "Kerrigan",
        "email": "sarahk@blitz.com",
        "admission": "2152-01-02T00:00:00",
        "marital_status": "MARRIED",
        "password": 'pass',
        "role": 'Employee',
    }
    entity = serializer.load(employee_dict)
    data_regression.check(dump(entity))


def test_one2one_pk_field(model, db_session, data_regression):
    seed_data(db_session, model)

    class EmployeeSerializerPrimaryKeyFields(ModelSerializer):
        password = Field(load_only=True)
        created_at = Field(dump_only=True)
        address = PrimaryKeyField(model.Address)
        company = PrimaryKeyField(model.Company)

    serializer = EmployeeSerializerPrimaryKeyFields(model.Employee)
    employee = db_session.query(model.Employee).get(2)
    serialized = serializer.dump(employee)
    data_regression.check(serialized, basename='test_one2one_pk_field')


def test_one2many_pk_field(model, db_session, data_regression):
    seed_data(db_session, model)

    class CompanySerializer(ModelSerializer):
        employees = PrimaryKeyField(model.Employee)

    serializer = CompanySerializer(model.Company)
    company = db_session.query(model.Company).get(5)
    serialized = serializer.dump(company)
    data_regression.check(serialized)

    serialized['employees'] = [2, 3]
    company = serializer.load(serialized, existing_model=company, session=db_session)
    assert company.employees[0] == db_session.query(model.Employee).get(2)
    assert company.employees[1] == db_session.query(model.Employee).get(3)


def test_property_serialization(model, db_session):
    seed_data(db_session, model)

    class EmployeeSerializerHybridProperty(ModelSerializer):
        full_name = Field(dump_only=True)

    serializer = EmployeeSerializerHybridProperty(model.Employee)
    serialized = serializer.dump(db_session.query(model.Employee).get(2))
    assert serialized['full_name'] is not None


def test_protected_field_default_creation(model, db_session):
    seed_data(db_session, model)

    serializer = ModelSerializer(model.Employee)
    employee = db_session.query(model.Employee).get(1)
    assert employee._salary == 400
    serialized = serializer.dump(employee)
    assert serialized.get('role') == 'Manager'
    assert serialized.get('_salary') is None

    entity = serializer.load(serialized, session=db_session)
    assert entity.role == 'Manager'
    assert entity._salary is None


def test_inherited_model_serialization(model, db_session):
    seed_data(db_session, model)

    serializer = PolymorphicModelSerializer(model.Employee)

    manager = db_session.query(model.Employee).get(1)
    assert isinstance(manager, model.Manager)

    serialized = serializer.dump(manager)
    assert serialized.get('role') == 'Manager'
    entity = serializer.load(serialized, session=db_session)
    assert hasattr(entity, 'manager_name')

    engineer = db_session.query(model.Employee).get(2)
    assert isinstance(engineer, model.Engineer)

    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Engineer'
    entity = serializer.load(serialized, session=db_session)
    assert hasattr(entity, 'engineer_name')

    engineer = db_session.query(model.Employee).get(4)
    assert isinstance(engineer, model.SpecialistEngineer)

    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Specialist Engineer'
    entity = serializer.load(serialized, session=db_session)
    assert hasattr(entity, 'specialization')


def test_nested_inherited_model_serialization(model, db_session):
    seed_data(db_session, model)

    serializer = PolymorphicModelSerializer(model.Engineer)

    engineer = db_session.query(model.Employee).get(2)
    assert isinstance(engineer, model.Engineer)
    serialized = serializer.dump(engineer)
    assert serialized.get('role') == 'Engineer'
    assert 'specialization' not in serialized.keys()

    specialist_engineer = db_session.query(model.Employee).get(4)
    assert isinstance(specialist_engineer, model.SpecialistEngineer)
    serialized = serializer.dump(specialist_engineer)
    assert serialized.get('role') == 'Specialist Engineer'
    assert 'specialization' in serialized.keys()
    assert serialized.get('specialization') == 'Mechanical'


def test_creation_only_flag(model, db_session):
    seed_data(db_session, model)

    class EmployeeSerializerCreationOnlyField(ModelSerializer):
        password = Field(load_only=True)
        created_at = Field(dump_only=True)
        email = Field(creation_only=True)

    serializer = EmployeeSerializerCreationOnlyField(model.Employee)

    serialized = {
        "password": "some",
        "email": "spoc@cap.co",
        "firstname": "S'Chn",
        "lastname": "Spock",
        "role": "Employee",
    }

    employee = serializer.load(serialized)
    db_session.add(employee)
    db_session.commit()

    assert employee.id is not None
    assert employee.email == 'spoc@cap.co'
    assert employee.firstname == "S'Chn"
    assert employee.lastname == 'Spock'

    serialized = {
        "password": "some",
        "email": "other_spoc@cap.co",
        "firstname": "Other",
        "lastname": "Spock",
        "role": "Employee",
    }

    changed_employee = serializer.load(serialized, existing_model=employee)

    assert changed_employee.email == 'spoc@cap.co'
    assert employee.firstname == 'Other'


def test_dump_choice_type(model, db_session, data_regression):
    seed_data(db_session, model)

    tychus = db_session.query(model.Employee).get(3)
    serializer = ModelSerializer(model.Employee)
    dump = serializer.dump(tychus)
    data_regression.check(dump, basename='test_dump_choice_type')


def test_load_choice_type(model, db_session):
    seed_data(db_session, model)

    json = {
        "password": "some",
        "email": "other_spoc@cap.co",
        "firstname": "Other",
        "lastname": "Spock",
        "role": "Employee",
        "contract_type": "Other",
    }

    serializer = ModelSerializer(model.Employee)
    loaded = serializer.load(json)
    db_session.add(loaded)
    db_session.commit()

    assert loaded.contract_type == model.ContractType.OTHER

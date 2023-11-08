import pytest

from serialchemy import func


@pytest.fixture(autouse=True)
def seed_data(model, db_session):
    company = model.Company(id=5, name='Terrans', location='Korhal')
    employee = model.Employee(
        id=2,
        firstname='Sarah',
        lastname='Kerrigan',
        email='some@email.com',
        password='somepass',
        role='Employee',
        company=company,
        marital_status=model.MaritalStatus.DIVORCED
    )
    db_session.add(employee)
    db_session.commit()


def test_dump(model, db_session, data_regression):
    employee = db_session.query(model.Employee).get(2)
    serial = func.dump(employee, nest_foreign_keys=True)
    data_regression.check(serial, basename='test_dump')


def test_load(model, db_session):
    data = dict(
        email='some@email.com',
        role='Employee',
        firstname='Sarah',
        lastname='Kerrigan',
        company=dict(location='some', name='Terrans'),
    )
    employee = func.load(data, model.Employee, nest_foreign_keys=True)
    assert employee.role == "Employee"
    assert employee.firstname == "Sarah"
    assert employee.company_name == "Terrans"

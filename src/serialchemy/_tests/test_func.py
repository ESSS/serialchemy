import pytest

from serialchemy import func
from serialchemy._tests.sample_model import Company, Employee


@pytest.fixture(autouse=True)
def seed_data(db_session):
    company = Company(id=5, name='Terrans', location='Korhal')
    employee = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)
    db_session.add(employee)
    db_session.commit()


def test_dump(db_session, data_regression):
    employee = db_session.query(Employee).get(2)
    serial = func.dump(employee, nest_foreign_keys=True)
    data_regression.check(serial)


def test_load(db_session):
    data = dict(firstname='Sarah', lastname='Kerrigan', company=dict(name='Terrans'))
    employee = func.load(data, Employee, nest_foreign_keys=True)
    assert employee.role == "Employee"
    assert employee.firstname == "Sarah"
    assert employee.company_name == "Terrans"

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import column_property, relationship

Base = declarative_base()


class Company(Base):
    __tablename__ = 'Company'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Employee(Base):
    __tablename__ = 'Employee'

    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    admission = Column(DateTime, default=datetime(2000, 1, 1))
    company_id = Column(ForeignKey('Company.id'))
    company = relationship(Company)
    company_name = column_property(select([Company.name]).where(Company.id == company_id))
    password = Column(String)


def test_example_1(db_session):
    from serialchemy import ModelSerializer

    emp = Employee(fullname='Roberto Silva', admission=datetime(2019, 4, 2))
    serializer = ModelSerializer(Employee)
    serializer.dump(emp)

    new_employee = {'fullname': 'Jobson Gomes', 'admission': '2018-02-03T00:00:00'}
    serializer.load(new_employee)

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property, object_session, relationship

from serialchemy.model_serializer import ModelSerializer
from serialchemy.field import Field
from serialchemy.nested_fields import NestedModelField, NestedModelListField
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Company(Base):

    __tablename__ = 'Company'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    employees = relationship("Employee", lazy='dynamic')


class Department(Base):

    __tablename__ = 'Department'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Address(Base):

    __tablename__ = 'Address'

    id = Column(Integer, primary_key=True)
    street = Column(String)
    number = Column(String)
    zip = Column(String)
    city = Column(String)
    state = Column(String)


class ContactType(Base):

    __tablename__ = 'ContactType'

    id = Column(Integer, primary_key=True)
    label = Column(String(15))


class Contact(Base):

    __tablename__ = 'Contact'

    id = Column(Integer, primary_key=True)
    type = relationship(ContactType)
    type_id = Column(ForeignKey('ContactType.id'))
    value = Column(String)
    employee_id = Column(ForeignKey('Employee.id'))


class Employee(Base):

    __tablename__ = 'Employee'

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    admission = Column(DateTime, default=datetime(2000, 1, 1))
    company_id = Column(ForeignKey('Company.id'))
    company = relationship(Company, back_populates='employees')
    company_name = column_property(
        select([Company.name]).where(Company.id == company_id)
    )
    address_id = Column(ForeignKey('Address.id'))
    address = relationship(Address)
    departments = relationship('Department', secondary='employee_department')
    contacts = relationship(Contact, cascade='all, delete-orphan')

    password = Column(String)
    created_at = Column(DateTime, default=datetime(2000, 1, 2))

    @property
    def colleagues(self):
        return object_session(self).query(Employee).filter(Employee.company_id == self.company_id)

    @hybrid_property
    def full_name(self):
        return " ".join([self.firstname, self.lastname])


employee_department = Table('employee_department', Base.metadata,
    Column('employee_id', Integer, ForeignKey('Employee.id')),
    Column('department_id', Integer, ForeignKey('Department.id'))
)


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)
    contacts = NestedModelListField(Contact)

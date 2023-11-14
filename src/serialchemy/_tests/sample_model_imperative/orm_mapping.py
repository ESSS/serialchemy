from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship
from sqlalchemy.sql import sqltypes
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Float
from sqlalchemy_utils import ChoiceType

from serialchemy._tests.sample_model_imperative.model import Address
from serialchemy._tests.sample_model_imperative.model import Company
from serialchemy._tests.sample_model_imperative.model import Contact
from serialchemy._tests.sample_model_imperative.model import ContactType
from serialchemy._tests.sample_model_imperative.model import ContractType
from serialchemy._tests.sample_model_imperative.model import MaritalStatus
from serialchemy._tests.sample_model_imperative.model import Department
from serialchemy._tests.sample_model_imperative.model import Employee
from serialchemy._tests.sample_model_imperative.model import Engineer
from serialchemy._tests.sample_model_imperative.model import Manager
from serialchemy._tests.sample_model_imperative.model import SpecialistEngineer

mapper_registry = registry()


mapper_registry.map_imperatively(
    ContactType,
    Table(
        'ContactType',
        mapper_registry.metadata,
        Column('id', Integer, primary_key=True),
        Column('street', String),
        Column('number', String),
        Column('zip', String),
        Column('city', String),
        Column('state', String),
    ),
)

company_table = Table(
    "Company",
    mapper_registry.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('location', String),
    Column('master_engeneer_id', Integer, ForeignKey('SpecialistEngineer.id')),
    Column('master_manager_id', Integer, ForeignKey('Manager.id')),
)
mapper_registry.map_imperatively(
    Company,
    company_table,
    properties={
        'employees': relationship('Employee', lazy='dynamic'),
        'master_engeneer': relationship(
            'SpecialistEngineer', foreign_keys=[company_table.c.master_engeneer_id]
        ),
        'master_manager': relationship('Manager', foreign_keys=[company_table.c.master_manager_id]),
    },
)
mapper_registry.map_imperatively(
    Department,
    Table(
        'Department',
        mapper_registry.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
    ),
)
mapper_registry.map_imperatively(
    Address,
    Table(
        'Address',
        mapper_registry.metadata,
        Column('id', Integer, primary_key=True),
        Column('street', String),
        Column('number', String),
        Column('zip', String),
        Column('city', String),
        Column('state', String),
    ),
)
mapper_registry.map_imperatively(
    Contact,
    Table(
        'Contact',
        mapper_registry.metadata,
        Column('id', Integer, primary_key=True),
        Column('value', String),
        Column('employee_id', ForeignKey('Employee.id')),
        Column('type_id', ForeignKey('ContactType.id')),
    ),
    properties={
        'type': relationship(ContactType),
        'employee': relationship('Employee'),
    },
)

employee_department = Table(
    'employee_department',
    mapper_registry.metadata,
    Column('employee_id', Integer, ForeignKey('Employee.id')),
    Column('department_id', Integer, ForeignKey('Department.id')),
)

employee_table = Table(
    'Employee',
    mapper_registry.metadata,
    Column('id', Integer, primary_key=True),
    Column('firstname', String),
    Column('lastname', String),
    Column('email', String),
    Column('admission', Date),
    Column('role', String),
    Column('_salary', Float),
    Column('password', String),
    Column('created_at', DateTime),
    Column('company_id', ForeignKey('Company.id')),
    Column('address_id', ForeignKey('Address.id')),
    Column('contract_type', ChoiceType(ContractType)),
    Column('marital_status', sqltypes.Enum(MaritalStatus)),
)


mapper_registry.map_imperatively(
    Employee,
    employee_table,
    properties={
        'company': relationship(Company, back_populates='employees'),
        'address': relationship(Address),
        'departments': relationship(Department, secondary='employee_department'),
        'contacts': relationship(Contact, cascade='all, delete-orphan'),
    },
    polymorphic_identity='Employee',
    polymorphic_on=employee_table.c.role,
)
mapper_registry.map_imperatively(
    Engineer,
    Table(
        'Engineer',
        mapper_registry.metadata,
        Column('eng_id', Integer, ForeignKey('Employee.id'), key='id', primary_key=True),
        Column('engineer_name', String(30)),
    ),
    inherits=Employee,
    polymorphic_identity='Engineer',
    polymorphic_on=employee_table.c.role,
)
mapper_registry.map_imperatively(
    SpecialistEngineer,
    Table(
        'SpecialistEngineer',
        mapper_registry.metadata,
        Column('esp_id', Integer, ForeignKey('Engineer.id'), key='id', primary_key=True),
        Column('specialization', String(30)),
    ),
    inherits=Engineer,
    polymorphic_identity='Specialist Engineer',
)
mapper_registry.map_imperatively(
    Manager,
    Table(
        'Manager',
        mapper_registry.metadata,
        Column('id', Integer, ForeignKey('Employee.id'), primary_key=True),
        Column('manager_name', String(30)),
    ),
    inherits=Employee,
    polymorphic_identity='Manager',
)

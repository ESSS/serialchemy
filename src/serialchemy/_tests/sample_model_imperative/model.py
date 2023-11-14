from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import List
from typing import Optional


@dataclass
class Company:

    name: str
    location: str
    id: Optional[int] = None
    master_engeneer: Optional['SpecialistEngineer'] = None
    master_manager: Optional['Manager'] = None
    employees: List['Employee'] = field(default_factory=list)


@dataclass
class Department:

    id: int
    name: str


@dataclass
class Address:

    street: str
    number: str
    city: str
    state: str
    id: Optional[int] = None
    zip: Optional[str] = None


@dataclass
class ContactType:

    label: str
    id: Optional[int] = None


@dataclass
class Contact:

    type: ContactType
    value: str
    employee: 'Employee'
    id: Optional[int] = None


class ContractType(Enum):

    EMPLOYEE = 'Employee'
    CONTRACTOR = 'Contractor'
    OTHER = 'Other'


class MaritalStatus(Enum):
    SINGLE = 'Single'
    MARRIED = 'Married'
    DIVORCED = 'Divorced'


@dataclass
class Employee:

    firstname: str
    lastname: str
    email: str
    role: str

    password: Optional[str] = None
    address: Optional[Address] = None
    contract_type: Optional[ContractType] = None
    marital_status: Optional[MaritalStatus] = None
    company: Optional[Company] = None
    _salary: Optional[float] = None
    id: Optional[int] = None
    admission: datetime = datetime(2000, 1, 1)
    created_at: datetime = datetime(2000, 1, 2)
    departments: List[Department] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)

    @property
    def company_name(self):
        return self.company.name

    @property
    def full_name(self):
        return " ".join([self.firstname, self.lastname])


@dataclass
class Engineer(Employee):
    engineer_name: Optional[str] = None


@dataclass
class SpecialistEngineer(Engineer):
    specialization: Optional[str] = None


@dataclass
class Manager(Employee):
    manager_name: Optional[str] = None

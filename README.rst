======================================================================
Serialchemy
======================================================================


.. image:: https://img.shields.io/pypi/v/serialchemy.svg
    :target: https://pypi.python.org/pypi/serialchemy

.. image:: https://img.shields.io/pypi/pyversions/serialchemy.svg
    :target: https://pypi.org/project/serialchemy

.. image:: https://github.com/ESSS/serialchemy/workflows/build/badge.svg
    :target: https://github.com/ESSS/serialchemy/actions

.. image:: https://codecov.io/gh/ESSS/serialchemy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ESSS/serialchemy

.. image:: https://img.shields.io/readthedocs/serialchemy.svg
    :target: https://serialchemy.readthedocs.io/en/latest/

.. image:: https://sonarcloud.io/api/project_badges/measure?project=ESSS_serialchemy&metric=alert_status
    :target: https://sonarcloud.io/project/overview?id=ESSS_serialchemy


SQLAlchemy model serialization.
===============================

Motivation
----------

**Serialchemy** was developed as a module of Flask-RESTAlchemy_, a lib to create Restful APIs
using Flask and SQLAlchemy. We first tried marshmallow-sqlalchemy_, probably the most
well-known lib for SQLAlchemy model serialization, but we faced `issues related to nested
models <https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67>`_. We also think
that is possible to build a simpler and more maintainable solution by having SQLAlchemy_ in
mind from the ground up, as opposed to marshmallow-sqlalchemy_ that had to be
designed and built on top of marshmallow_.

.. _SQLAlchemy: www.sqlalchemy.org
.. _marshmallow-sqlalchemy: http://marshmallow-sqlalchemy.readthedocs.io
.. _marshmallow: https://marshmallow.readthedocs.io
.. _Flask-RESTAlchemy: https://github.com/ESSS/flask-restalchemy

How to Use it
-------------

Serializing Generic Types
.........................

Suppose we have an `Employee` SQLAlchemy_ model declared:

.. code-block:: python

    class Employee(Base):
        __tablename__ = "Employee"

        id = Column(Integer, primary_key=True)
        fullname = Column(String)
        admission = Column(DateTime, default=datetime(2000, 1, 1))
        company_id = Column(ForeignKey("Company.id"))
        company = relationship(Company)
        company_name = column_property(
            select([Company.name]).where(Company.id == company_id)
        )
        password = Column(String)

`Generic Types`_ are automatically serialized by `ModelSerializer`:

.. code-block:: python

    from serialchemy import ModelSerializer

    emp = Employee(fullname="Roberto Silva", admission=datetime(2019, 4, 2))

    serializer = ModelSerializer(Employee)
    serializer.dump(emp)

    # >>
    {
        "id": None,
        "fullname": "Roberto Silva",
        "admission": "2019-04-02T00:00:00",
        "company_id": None,
        "company_name": None,
        "password": None,
    }

New items can be deserialized by the same serializer:

.. code-block:: python

    new_employee = {"fullname": "Jobson Gomes", "admission": "2018-02-03"}
    serializer.load(new_employee)

    # >> <Employee object at 0x000001C119DE3940>

Serializers do not commit into the database. You must do this by yourself:

.. code-block:: python

    emp = serializer.load(new_employee)
    session.add(emp)
    session.commit()

.. _`Generic Types`: https://docs.sqlalchemy.org/en/rel_1_2/core/type_basics.html#generic-types

Custom Serializers
..................

For anything beyond `Generic Types`_ we must extend the `ModelSerializer` class:

.. code-block:: python

    class EmployeeSerializer(ModelSerializer):

        password = Field(load_only=True)  # passwords should be only deserialized
        company = NestedModelField(Company)  # dump company as nested object


    serializer = EmployeeSerializer(Employee)
    serializer.dump(emp)
    # >>
    {
        "id": 1,
        "fullname": "Roberto Silva",
        "admission": "2019-04-02T00:00:00",
        "company": {"id": 3, "name": "Acme Co"},
    }


Extend Polymorphic Serializer
+++++++++++++++++++++++++++++
One of the possibilities is to serialize SQLalchemy joined table inheritance and
it child tables as well. To do such it's necessary to set a variable with
the desired model class name. Take this `Employee` class with for instance and let us
assume it have a joined table inheritance:

.. code-block:: python

    class Employee(Base):
        ...
        type = Column(String(50))

        __mapper_args__ = {"polymorphic_identity": "employee", "polymorphic_on": type}


    class Engineer(Employee):
        __tablename__ = "Engineer"
        id = Column(Integer, ForeignKey("employee.id"), primary_key=True)
        association = relationship(Association)

        __mapper_args__ = {
            "polymorphic_identity": "engineer",
        }

To use a extended `ModelSerializer` class on the `Engineer` class, you should create
the serializer as it follows:

.. code-block:: python

    class EmployeeSerializer(
        PolymorphicModelSerializer
    ):  # Since this class will be polymorphic

        password = Field(load_only=True)
        company = NestedModelField(Company)


    class EngineerSerializer(EmployeeSerializer):
        __model_class__ = Engineer  # This is the table Serialchemy will refer to
        association = NestedModelField(Association)

Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to serialchemy, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/ESSS/serialchemy/blob/master/CONTRIBUTING.rst


Release
-------
A reminder for the maintainers on how to make a new release.

Note that the VERSION should folow the semantic versioning as X.Y.Z Ex.: v1.0.5

Create a release-VERSION branch from upstream/master.
Update CHANGELOG.rst.
Push a branch with the changes.
Once all builds pass, push a VERSION tag to upstream. Ex: git tag v1.0.5; git push origin --tags
Merge the PR.

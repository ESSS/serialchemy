======================================================================
Serialchemy
======================================================================

.. TODO: Publish to PyPi
    .. image:: https://img.shields.io/pypi/v/serialchemy.svg
    :target: https://pypi.python.org/pypi/serialchemy
    .. image:: https://img.shields.io/pypi/pyversions/serialchemy.svg
    :target: https://pypi.org/project/serialchemy

.. image:: https://img.shields.io/travis/ESSS/serialchemy.svg
    :target: https://travis-ci.org/ESSS/serialchemy

.. image:: https://ci.appveyor.com/api/projects/status/github/ESSS/serialchemy?branch=master
    :target: https://ci.appveyor.com/project/ESSS/serialchemy/?branch=master&svg=true

.. image:: https://codecov.io/gh/ESSS/serialchemy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ESSS/serialchemy

.. image:: https://img.shields.io/readthedocs/pip.svg
    :target: https://serialchemy.readthedocs.io/en/latest/

SQLAlchemy model serialization.

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

Suppose we have an `Employee` SQLAlchemy_ model declared: ::

    class Employee(Base):
        __tablename__ = 'Employee'

        id = Column(Integer, primary_key=True)
        fullname = Column(String)
        admission = Column(DateTime, default=datetime(2000, 1, 1))
        company_id = Column(ForeignKey('Company.id'))
        company = relationship(Company)
        company_name = column_property(
            select([Company.name]).where(Company.id == company_id)
        )
        password = Column(String)

`Generic Types`_ are automatically serialized by `ModelSerializer`: ::

    from serialchemy import ModelSerializer

    emp = Employee(fullname='Roberto Silva', admission=datetime(2019, 4, 2))

    serializer = ModelSerializer(Employee)
    serializer.dump(emp)

    >> {'id': None,
        'fullname': 'Roberto Silva',
        'admission': '2019-04-02T00:00:00',
        'company_id': None,
        'company_name': None,
        'password': None
        }

New items can be deserialized by the same serializer: ::

    new_employee = {'fullname': 'Jobson Gomes', 'admission': '2018-02-03'}
    serializer.load(new_employee)
    >> <Employee object at 0x000001C119DE3940>

Serializers do not commit into the database. You must do this by yourself: ::

    emp = serializer.load(new_employee)
    session.add(emp)
    session.commit()

.. _`Generic Types`: https://docs.sqlalchemy.org/en/rel_1_2/core/type_basics.html#generic-types

Custom Serializers
..................

For anything beyond `Generic Types`_ we must extend the `ModelSerializer` class: ::

    class EmployeeSerializer(ModelSerializer):

        password = Field(load_only=True)     # passwords should be only deserialized
        company = NestedModelField(Company)  # dump company as nested object

    serializer = EmployeeSerializer(Employee)
    serializer.dump(emp)

    >> {'id': 1,
        'fullname': 'Roberto Silva',
        'admission': '2019-04-02T00:00:00',
        'company': {'id': 3,
                    'name': 'Acme Co'
                   }
        }


Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to serialchemy, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/ESSS/serialchemy/blob/master/CONTRIBUTING.rst


Release
-------
A reminder for the maintainers on how to make a new release.

Note that the VERSION should folow the semantic versioning as X.Y.Z
Ex.: v1.0.5

1. Create a ``release-VERSION`` branch from ``upstream/master``.
2. Update ``CHANGELOG.rst``.
3. Push a branch with the changes.
4. Once all builds pass, push a ``VERSION`` tag to ``upstream``.
5. Merge the PR.

=======
History
=======

0.3.0 (2019-17-07)
------------------
* Add the composite fields to list of properties of model, to serialize that fields if it type is in EXTRA_SERIALIZERS.
* Fix error for SQLAlchemy composite attributes
* Added free functions dump and load so users can quickly dump a SQLAlchemy model without having to instancialize
  ModelSerializer.

0.2.0 (2019-03-22)
------------------

* Fix: Error when deserializing of nested models when SQLAlchemy model primary
  key attribute name differs from the column name
* Allow EXTRA_SERIALIZERS to be defined in runtime
* Check if a session was given when serializing/deserializing nested fields

0.1.0 (2019-02-12)
------------------

* First release on PyPI.

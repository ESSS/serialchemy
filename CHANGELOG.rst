History
=======

0.4.0 (2013-12-11)
------------------
* Fix to get model attribute name instead of table column name on polymorphic serializer
* Extends the PolymorphicModelSerializer to accept also column descriptors when searching
  for the polymorphic column key.
* Add support for serialization of Python Enums
* Change PolymorphicModelSerializer to support inherited models of inherited models
* Change Field to use a default serializer for not None values
* Added support for sqlalchemy 1.4
* Add EnumKeySerializer

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

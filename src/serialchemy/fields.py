from typing import Union

from sqlalchemy.orm.dynamic import AppenderMixin


class Field(object):
    """
    Configure a ModelSerializer field
    """

    def __init__(self, dump_only=False, load_only=False, serializer=None):
        self.dump_only = dump_only
        self.load_only = load_only
        self._serializer = serializer

    @property
    def serializer(self):
        return self._serializer

    def dump(self, value):
        if value and self.serializer:
            return self.serializer.dump(value)
        else:
            return value

    def load(self, serialized, session=None):
        if serialized and self.serializer:
            return self.serializer.load(serialized, session=session)
        else:
            return serialized


class NestedModelListField(Field):
    """
    A field to Dump and Update nested model list.
    """

    def __init__(self, declarative_class, **kw):
        from .modelserializer import ModelSerializer

        super().__init__(**kw)
        if self._serializer is None:
            self._serializer = ModelSerializer(declarative_class)

    def load(self, serialized, session=None):
        if not serialized:
            return []
        class_mapper = self.serializer.model_class
        pk_attr = get_pk_attr_name(class_mapper)
        models = []
        for item in serialized:
            pk = item.get(pk_attr)
            if pk:
                # Serialized object has a primary key, so we load an existing model from the database
                # instead of creating one
                existing_model = session.query.get(pk)
                updated_model = self.serializer.load(item, existing_model, session=session)
                models.append(updated_model)
            else:
                # No primary key, just create a new model entity
                model = self.serializer.load(item)
                models.append(model)
        return models

    def dump(self, value):
        if value and self.serializer:
            return [self.serializer.dump(item) for item in value]
        else:
            return value


class NestedModelField(Field):
    """
    A field to Dump and Update nested models.
    """

    def __init__(self, declarative_class, **kw):
        from .modelserializer import ModelSerializer

        super().__init__(**kw)
        if self._serializer is None:
            self._serializer = ModelSerializer(declarative_class)

    def load(self, serialized, session=None):
        if not serialized:
            return None
        class_mapper = self.serializer.model_class
        pk_attr = get_pk_attr_name(class_mapper)
        pk = serialized.get(pk_attr)
        if pk:
            # Serialized object has a primary key, so we load an existing model from the database
            # instead of creating one
            existing_model = session.query.get(pk)
            return self.serializer.load(serialized, existing_model, session=session)
        else:
            # No primary key, just create a new model entity
            return self.serializer.load(serialized, session=session)


class NestedAttributesField(Field):
    """
    A read-only field that dump nested object attributes.
    """
    from .serializer import Serializer

    class NestedAttributesSerializer(Serializer):

        def __init__(self, attributes, many):
            self.attributes = attributes
            self.many = many

        def dump(self, value):
            if self.many:
                serialized = [self._dump_item(item) for item in value]
            else:
                return self._dump_item(value)
            return serialized

        def _dump_item(self, item):
            serialized = {}
            for attr_name in self.attributes:
                serialized[attr_name] = getattr(item, attr_name)
            return serialized

        def load(self, serialized, session=None):
            raise NotImplementedError()

    def __init__(self, attributes: Union[tuple, dict], many=False):
        serializer = self.NestedAttributesSerializer(attributes, many)
        super().__init__(dump_only=True, serializer=serializer)


class PrimaryKeyField(Field):
    """
    Convert relationships in a list of primary keys (for serialization and deserialization).
    """
    from .serializer import Serializer

    class PrimaryKeySerializer(Serializer):

        def __init__(self, declarative_class):
            self.declarative_class = declarative_class
            self._pk_column = get_model_pk(self.declarative_class)

        def load(self, serialized, session=None):
            pk_column = self._pk_column
            query_results = session.query(self.declarative_class).filter(pk_column.in_(serialized)).all()
            if len(serialized) != len(query_results):
                raise ValueError("Not all primary keys found for '{}'".format(self._pk_column))
            return query_results

        def dump(self, value):
            pk_column = self._pk_column
            if is_tomany_attribute(value):
                serialized = [getattr(item, pk_column.key) for item in value]
            else:
                return getattr(value, pk_column.key)
            return serialized

    def __init__(self, declarative_class, **kw):
        super().__init__(serializer=self.PrimaryKeySerializer(declarative_class), **kw)


def get_pk_attr_name(declarative_model):
    """
    Get the primary key attribute name from a Declarative model class

    :param Type[DeclarativeMeta] declarative_class: a Declarative class

    :return: str: a Column name
    """
    primary_keys = declarative_model.__mapper__.primary_key
    assert len(primary_keys) == 1, "Nested object must have exactly one primary key"
    pk_name = primary_keys[0].key
    return pk_name


def get_model_pk(declarative_class):
    """
    Get the primary key Column object from a Declarative model class

    :param Type[DeclarativeMeta] declarative_class: a Declarative class

    :rtype: Column
    """
    primary_keys = declarative_class.__mapper__.primary_key
    assert len(primary_keys) == 1, "Nested object must have exactly one primary key"
    return primary_keys[0]


def is_tomany_attribute(value):
    """
    Check if the Declarative relationship attribute represents a to-many relationship.

    :param value: a SQLAlchemy Declarative class relationship attribute

    :rtype: bool
    """
    return isinstance(value, (list, AppenderMixin))

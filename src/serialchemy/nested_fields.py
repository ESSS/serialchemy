from warnings import warn

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.dynamic import AppenderMixin

from .field import Field
from .model_serializer import ModelSerializer
from .serializer import Serializer


class SessionBasedField(Field):
    """
    Base class for fields that requires a SQLAlchemy session
    """

    def load(self, serialized, session):
        raise NotImplementedError('load method not implemented')


class PrimaryKeyField(SessionBasedField):
    """
    Convert relationships in a list of primary keys (for serialization and deserialization).
    """

    def __init__(self, model_class, **kwargs):
        super().__init__(**kwargs)
        self.model_class = model_class
        self._pk_column = get_model_pk_column(self.model_class)

    def load(self, serialized, session):
        pk_column = self._pk_column
        query_results = session.query(self.model_class).filter(pk_column.in_(serialized)).all()
        if len(serialized) != len(query_results):
            warn(
                "Not all primary keys found for '{}.{}'".format(
                    self.model_class.__name__, self._pk_column
                )
            )
        return query_results

    def dump(self, value):
        def is_tomany_attribute(column):
            """
            Check if the Declarative relationship attribute represents a to-many relationship.
            """
            return isinstance(column, (list, AppenderMixin))

        pk_column = self._pk_column
        if is_tomany_attribute(value):
            serialized = [getattr(item, pk_column.key) for item in value]
        else:
            return getattr(value, pk_column.key)
        return serialized


class NestedModelField(SessionBasedField):
    """
    A field to Dump and Update nested models.
    """

    def __init__(self, model_class, **kwargs):
        if kwargs.get('serializer') is None:
            kwargs['serializer'] = ModelSerializer(model_class)
        super().__init__(**kwargs)

    def load(self, serialized, session):
        if not serialized:
            return None
        class_mapper = self.serializer.model_class
        pk_attr = get_model_pk_attr_name(class_mapper)
        pk = serialized.get(pk_attr)
        if pk:
            # Serialized object has a primary key, so we load an existing model from the database
            # instead of creating one
            if session is None:
                raise RuntimeError("Session object is required to deserialize a nested object")
            with session.no_autoflush:
                existing_model = session.query(class_mapper).get(pk)
            return self.serializer.load(serialized, existing_model, session=session)
        else:
            # No primary key, just create a new model entity
            return self.serializer.load(serialized, session=session)


class NestedModelListField(SessionBasedField):
    """
    A field to Dump and Update nested model list.
    """

    def __init__(self, model_class, **kwargs):
        if kwargs.get('serializer') is None:
            kwargs['serializer'] = ModelSerializer(model_class)
        super().__init__(**kwargs)

    def load(self, serialized, session):
        if not serialized:
            return []
        class_mapper = self.serializer.model_class
        pk_attr = get_model_pk_attr_name(class_mapper)
        models = []
        for item in serialized:
            pk = item.get(pk_attr)
            if pk:
                # Serialized object has a primary key, so we load an existing model from the database
                # instead of creating one
                if session is None:
                    raise RuntimeError("Session object is required to deserialize a nested object")
                existing_model = session.query(class_mapper).get(pk)
                updated_model = self.serializer.load(item, existing_model, session=session)
                models.append(updated_model)
            else:
                # No primary key, just create a new model entity
                model = self.serializer.load(item, session=session)
                models.append(model)
        return models

    def dump(self, value):
        return [self.serializer.dump(item) for item in value] if value is not None else []


class NestedAttributesField(Field):
    """
    A read-only field that dump selected nested object attributes.
    """

    def __init__(self, attributes, many=False):
        """

        :param Union[attr|dict] attributes:
        :param many:
        """
        serializer = NestedAttributesSerializer(attributes, many)
        super().__init__(dump_only=True, serializer=serializer)


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


def get_model_pk_attr_name(model_class):
    """
    Get the primary key attribute name from a Declarative model class

    :param Type[DeclarativeMeta] model_class: a Declarative class

    :return: str: the attribute name for the column with primary key
    """
    primary_key_columns = list(
        filter(lambda attr_col: attr_col[1].primary_key, class_mapper(model_class).columns.items())
    )
    primary_key_names = set(column[0] for column in primary_key_columns)
    if len(primary_key_names) == 1:
        return primary_key_names.pop()
    elif len(primary_key_names) < 1:
        raise RuntimeError(f"Couldn't find attribute for {model_class}")
    else:
        raise RuntimeError("Multiple primary keys still not supported")


def get_model_pk_column(model_class):
    """
    Get the primary key Column object from a Declarative model class

    :param Type[DeclarativeMeta] model_class: a Declarative class

    :rtype: Column
    """
    primary_keys = class_mapper(model_class).primary_key
    assert len(primary_keys) == 1, "Nested object must have exactly one primary key"
    return primary_keys[0]

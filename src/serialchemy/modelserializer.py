from serialchemy.enumserializer import EnumSerializer
from serialchemy.serializer_checks import is_datetime_column, is_enum_column

from .datetimeserializer import DateTimeSerializer
from .field import Field
from .serializer import Serializer


class ModelSerializer(Serializer):
    """
    Serializer for SQLAlchemy Declarative classes
    """

    EXTRA_SERIALIZERS = [
        (DateTimeSerializer, is_datetime_column),
        (EnumSerializer, is_enum_column)
    ]

    def __init__(self, model_class):
        """
        :param Type[DeclarativeMeta] model_class: the SQLAlchemy mapping class to be serialized
        """
        self._mapper_class = model_class
        self._fields = self._get_declared_fields()
        # Collect columns not declared in the serializer
        for column_name, column in self.model_columns.items():
            field = self._fields.setdefault(column_name, Field())
            if field.serializer is None:
                # If no serializer is defined, check if the column type has some serialized
                # registered in EXTRA_SERIALIZERS.
                for serializer_class, serializer_check in self.EXTRA_SERIALIZERS:
                    if serializer_check(column):
                        field._serializer = serializer_class(column)

    @property
    def model_class(self):
        return self._mapper_class

    @property
    def model_columns(self):
        return self._mapper_class.__mapper__.c

    @property
    def fields(self):
        return self._fields.copy()

    def dump(self, model):
        """
        Create a serialized dict from a Declarative model

        :param DeclarativeMeta model: the model to be serialized

        :rtype: dict
        """
        serial = {}
        for attr, field in self._fields.items():
            if field.load_only:
                continue
            value = getattr(model, attr) if hasattr(model, attr) else None
            if field:
                serialized = field.dump(value)
            else:
                serialized = value
            serial[attr] = serialized
        return serial

    def load(self, serialized, existing_model=None, session=None):
        """
        Instancialize a Declarative model from a serialized dict

        :param dict serialized: the serialized object.

        :param None|DeclarativeMeta existing_model: If given, the model will be updated with the serialized data.

        :param None|Session session: a SQLAlchemy session. Used only to load nested models

        :rtype: DeclarativeMeta
        """
        from .nested_fields import SessionBasedField

        if existing_model:
            model = existing_model
        else:
            model = self._mapper_class()
        for field_name, value in serialized.items():
            field = self._fields[field_name]
            if field.dump_only:
                continue
            if isinstance(field, SessionBasedField):
                deserialized = field.load(value, session=session)
            else:
                deserialized = field.load(value)
            setattr(model, field_name, deserialized)
        return model

    def get_model_name(self):
        """
        :rtype: str
        """
        return self._mapper_class.__name__

    @classmethod
    def _get_declared_fields(cls) -> dict:
        fields = {}
        # Fields should be only defined ModelSerializer subclasses,
        if cls is ModelSerializer:
            return fields
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            value = getattr(cls, attr_name)
            if isinstance(value, Field):
                fields[attr_name] = value
        return fields

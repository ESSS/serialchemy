from serialchemy.enumserializer import EnumSerializer, is_enum_field

from .datetimeserializer import DateTimeSerializer, is_datetime_field
from .fields import Field
from .serializer import Serializer


class ModelSerializer(Serializer):
    """
    Serializer for SQLAlchemy Declarative classes
    """

    def __init__(self, model_class):
        """
        :param Type[DeclarativeMeta] model_class: the SQLAlchemy mapping class to be serialized
        """
        self._mapper_class = model_class
        self._fields = self._get_declared_fields()
        # Collect columns not declared in the serializer
        self.session = None
        for column_name in self.model_columns.keys():
            field = self._fields.setdefault(column_name, Field())
            # Set a serializer for fields that can not be serialized by default
            if field.serializer is None:
                column = self.model_columns[column_name]
                if is_datetime_field(column):
                    field._serializer = DateTimeSerializer(column)
                elif is_enum_field(column):
                    field._serializer = EnumSerializer(column)

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

        :rtype: DeclarativeMeta
        """
        if existing_model:
            model = existing_model
        else:
            model = self._mapper_class()
        for field_name, value in serialized.items():
            field = self._fields[field_name]
            if field.dump_only:
                continue
            if field.serializer:
                if session:
                    field.serializer.session = session
                else:
                    field.serializer.session = self.session
            deserialized = field.load(value, session=session)
            setattr(model, field_name, deserialized)
        return model

    def get_model_name(self) -> str:
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

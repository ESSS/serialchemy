from serialchemy.enum_serializer import EnumSerializer
from serialchemy.serializer_checks import is_datetime_column, is_enum_column

from .datetime_serializer import DateTimeColumnSerializer
from .field import Field
from .serializer import Serializer


class ModelSerializer(Serializer):
    """
    Serializer for SQLAlchemy Declarative classes
    """

    EXTRA_SERIALIZERS = [
        (DateTimeColumnSerializer, is_datetime_column),
        (EnumSerializer, is_enum_column)
    ]

    def __init__(self, model_class):
        """
        :param Type[DeclarativeMeta] model_class: the SQLAlchemy mapping class to be serialized
        """
        self._mapper_class = model_class
        self._fields = self._get_declared_fields()
        # Collect columns not declared in the serializer
        for column_name in self.model_columns.keys():
            self._fields.setdefault(column_name, Field())

    @property
    def model_class(self):
        return self._mapper_class

    @property
    def model_columns(self):
        return self._mapper_class.__mapper__.c

    @property
    def fields(self):
        return self._fields

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
            value = getattr(model, attr, None)
            if field:
                self._assign_default_field_serializer(field, attr)
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
            model = self._create_model(serialized)
        for field_name, value in serialized.items():
            field = self._fields[field_name]
            if field.dump_only:
                continue
            self._assign_default_field_serializer(field, field_name)
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

    def _create_model(self, serialized):
        """
        Can be overridden in a derived class to customize model initialization.

        :param dict serialized: the serialized object

        :rtype: DeclarativeMeta
        """
        return self.model_class()

    def _assign_default_field_serializer(self, field, column_name):
        """
        If no serializer is defined, check if the column type has some serialized
        registered in EXTRA_SERIALIZERS.

        :param Field field: the field to assign default serializer

        :param str column_name: sqlalchemy column name on model
        """
        column = self.model_columns.get(column_name)
        if field.serializer is None and column is not None:
            for serializer_class, serializer_check in self.EXTRA_SERIALIZERS:
                if serializer_check(column):
                    field._serializer = serializer_class(column)

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

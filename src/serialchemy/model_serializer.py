import warnings

from sqlalchemy.ext.declarative import DeclarativeMeta

from serialchemy.enum_serializer import EnumSerializer
from serialchemy.serializer_checks import is_datetime_column, is_enum_column, is_date_column

from .datetime_serializer import DateTimeColumnSerializer, DateColumnSerializer
from .field import Field
from .serializer import Serializer


class ModelSerializer(Serializer):
    """
    Serializer for SQLAlchemy Declarative classes
    """

    EXTRA_SERIALIZERS = [
        (DateTimeColumnSerializer, is_datetime_column),
        (DateColumnSerializer, is_date_column),
        (EnumSerializer, is_enum_column)
    ]

    def __init__(self, model_class, nest_foreign_keys=False):
        """
        :param Type[DeclarativeMeta] model_class: the SQLAlchemy mapping class to be serialized
        """
        self._model_class = model_class
        self._fields = self._get_declared_fields()
        self._initialize_fields(nest_foreign_keys)

    @property
    def model_class(self):
        return self._model_class

    @property
    def model_columns(self):
        return self._model_class.__mapper__.c

    @property
    def model_composites(self):
        return self._model_class.__mapper__.composites

    @property
    def model_properties(self):
        model_properties = {}
        if self.model_columns:
            model_properties.update(self.model_columns)
        if self.model_composites:
            model_properties.update(self.model_composites)
        return model_properties

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
                self._assign_default_serializer(field, attr)
                serialized = field.dump(value)
            else:
                serialized = value
            serial[attr] = serialized
        return serial

    def load(self, serialized, existing_model=None, session=None):
        """
        Initialize a Declarative model from a serialized dict

        :param dict serialized: the serialized object.

        :param None|DeclarativeMeta existing_model: If given, the model will be updated with the serialized data.

        :param None|Session session: a SQLAlchemy session. Used only to load nested models
        """
        from .nested_fields import SessionBasedField

        if existing_model:
            model = existing_model
        else:
            model = self._create_model(serialized)
            assert model is not None, "ModelSerializer._create_model cannot return None"
        for field_name, value in serialized.items():
            if field_name not in self._fields:
                warnings.warn(f"Field '{field_name}' not defined for {self._model_class.__name__}")
                continue
            field = self._fields[field_name]
            if field.dump_only:
                continue
            if field.creation_only and existing_model:
                continue
            self._assign_default_serializer(field, field_name)
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
        return self._model_class.__name__

    def _create_model(self, serialized):
        """
        Can be overridden in a derived class to customize model initialization.

        :param dict serialized: the serialized object

        :rtype: DeclarativeMeta
        """
        return self.model_class()

    def _initialize_fields(self, nest_foreign_keys):
        """
        Collect columns not declared in the serializer
        """
        for attribute_name, attribute in self.model_properties.items():
            if attribute_name.startswith('_'):
                continue
            if nest_foreign_keys and attribute.foreign_keys:
                field_name, nested_field = self._create_nested_field_from_foreign_key(attribute)
                self._fields.setdefault(field_name, nested_field)
            else:
                self._fields.setdefault(attribute_name, Field())

    def _assign_default_serializer(self, field, property_name):
        """
        If no serializer is defined, check if the column type has some serializer
        registered in EXTRA_SERIALIZERS.

        :param Field field: the field to assign default serializer

        :param str property_name: sqlalchemy column name on model
        """
        model_property = self.model_properties.get(property_name)
        if field.serializer is None and model_property is not None:
            for serializer_class, serializer_check in self.EXTRA_SERIALIZERS:
                if serializer_check(model_property):
                    field._serializer = serializer_class(model_property)

    @classmethod
    def _get_declared_fields(cls) -> dict:
        fields = {}
        # Fields should be only defined ModelSerializer subclasses,
        if cls is ModelSerializer:
            return fields
        for attr_name in dir(cls):
            value = getattr(cls, attr_name)
            if isinstance(value, Field):
                fields[attr_name] = value
        return fields

    def _create_nested_field_from_foreign_key(self, column_object):
        """
        Create a NestedModelField for the given `column_object` that represents a foreign key.

        :param Column column_object: the model column object

        :rtype: Tuple[str, NestedModelField]
        """
        from serialchemy import NestedModelField

        try:
            fk_list = list(column_object.foreign_keys)
        except AttributeError:
            raise TypeError(f"{column_object} is not a foreign key Column")
        fk_column = fk_list[0].column
        for name, rp in self._model_class.__mapper__.relationships.items():
            if fk_column in rp.remote_side:
                nested_model_class = rp.argument
                return name, NestedModelField(nested_model_class)
        else:
            raise RuntimeError(f"Unexpected condition for {column_object}")

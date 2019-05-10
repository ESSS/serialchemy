from serialchemy.serializer import Serializer

class Field(object):
    """
    Configure a ModelSerializer field
    """

    def __init__(self, dump_only=False, load_only=False, creation_only=False, serializer=None):
        """
        :param bool dump_only: If True, field is not included on deserialization.

        :param bool load_only: If True, field is not included in serialization.

        :param bool creation_only: If True, the field is included in serialization only when the load creates a new
            entity, and is ignored when the load is updating an existent entity.

            Warning: If dump_only flag is True this flag has no effect.

        :param Serializer serializer: define a custom serializer for the field. If none,
            the field value is returned by dump.
        """
        self.dump_only = dump_only
        self.load_only = load_only
        self.creation_only = creation_only
        if serializer and not isinstance(serializer, Serializer):
            raise TypeError(f"'{serializer}' is not an instance of 'Serializer'")
        self._serializer = serializer

    @property
    def serializer(self):
        return self._serializer

    def dump(self, value):
        if value is not None and self.serializer:
            return self.serializer.dump(value)
        else:
            return value

    def load(self, serialized, **kw):
        if serialized and self.serializer:
            return self.serializer.load(serialized, **kw)
        else:
            return serialized

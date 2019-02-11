from .serializer import ColumnSerializer


class EnumSerializer(ColumnSerializer):

    def dump(self, value):
        if not value:
            return None
        return value.value

    def load(self, serialized, session=None):
        enum = getattr(self.column.type, 'enum_class')
        return enum(serialized)

from typing import Type

from enum import Enum

from .serializer import ColumnSerializer, Serializer


class EnumSerializer(ColumnSerializer):
    def dump(self, value):
        if not value:
            return None
        return value.value

    def load(self, serialized, session=None):
        enum = getattr(self.column.type, 'enum_class')
        return enum(serialized)

class EnumKeySerializer(Serializer):
    def __init__(self, enum_class: Type[Enum]) -> None:
        super().__init__()
        self.enum_class = enum_class

    def dump(self, value):
        if not value:
            return None
        return value.name

    def load(self, serialized, session=None):
        return self.enum_class[serialized]
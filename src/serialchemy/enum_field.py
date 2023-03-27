from serialchemy.enum_serializer import EnumKeySerializer
from serialchemy.field import Field


class EnumKeyField(Field):
    def __init__(self, enum_class, dump_only=False, load_only=False, creation_only=False):
        super().__init__(dump_only=dump_only, load_only=load_only, creation_only=creation_only, serializer=EnumKeySerializer(enum_class))
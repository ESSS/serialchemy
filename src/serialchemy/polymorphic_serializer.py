import enum
from sqlalchemy.orm import class_mapper

from serialchemy import ModelSerializer


def _get_identity(cls):
    identity_value = class_mapper(cls).polymorphic_identity
    if isinstance(identity_value, enum.Enum):
        return identity_value.value
    return identity_value


def _get_identity_key(cls):
    identityColumn = class_mapper(cls).polymorphic_on
    assert hasattr(identityColumn, 'key')
    column_db_name = identityColumn.key
    for attribute_name, attribute in class_mapper(cls).c.items():
        if attribute.key == column_db_name:
            return attribute_name
    raise AttributeError(
        f"'polymorphic_on' attribute set incorrectly, are you sure it should be {column_db_name}?"
    )


def has_sqlalchemy_polymorphic_decendants(cls):
    # if the class mapper has descendants, then it is a polymorphic structure and is not a leaf
    return len(class_mapper(cls).self_and_descendants) > 1


class PolymorphicModelSerializer(ModelSerializer):
    """
    Serializer for models that have a common base class. Can be used as serializer for endpoints that have objects
    from different classes (but have a common base)
    """

    def __init__(self, declarative_class):
        super().__init__(declarative_class)
        # maped = class_mapper(declarative_class)
        if has_sqlalchemy_polymorphic_decendants(declarative_class):
            self.is_polymorphic = True
            self.sub_serializers = self._get_sub_serializers(declarative_class)
            self.identity_key = _get_identity_key(declarative_class)
        else:
            self.is_polymorphic = False

    @classmethod
    def _get_sub_serializers(cls, declarative_class):

        serializers_sub_class_map = {
            sub_cls.get_identity(): sub_cls
            for sub_cls in cls.__subclasses__()
            if sub_cls.get_identity()
        }

        def get_subclasses(declarative_class):
            """Recursively finds all subclasses of the current class"""
            subclasses = declarative_class.__subclasses__()
            for s in subclasses:
                subclasses.extend(get_subclasses(s))
            return subclasses

        return {
            _get_identity(sub_cls): serializers_sub_class_map.get(_get_identity(sub_cls), cls)(
                sub_cls
            )
            for sub_cls in get_subclasses(declarative_class)
        }

    @classmethod
    def get_identity(cls):
        return _get_identity(cls.__model_class__) if hasattr(cls, '__model_class__') else None

    def load(self, serialized, existing_model=None, session=None):
        if self.is_polymorphic:
            model_identity = serialized.get(self.identity_key)
            if model_identity and self.sub_serializers.get(model_identity):
                return self.sub_serializers[model_identity].load(
                    serialized, existing_model, session
                )
        return super().load(serialized, existing_model, session)

    def dump(self, model):
        if self.is_polymorphic:
            model_identity = _get_identity(model.__class__)
            if model_identity in self.sub_serializers:
                return self.sub_serializers[model_identity].dump(model)
        return super().dump(model)

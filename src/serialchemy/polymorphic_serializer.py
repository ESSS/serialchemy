from sqlalchemy import Column

from serialchemy import ModelSerializer


def _get_identity(cls):
    args = getattr(cls, '__mapper_args__', None)
    return args.get('polymorphic_identity') if args is not None else None


def _get_identity_key(cls):
    identityColumn = cls.__mapper_args__['polymorphic_on']
    assert isinstance(identityColumn, Column)
    column_db_name =  identityColumn.key
    for attribute_name, attribute in cls.__mapper__.c.items():
        if attribute_name.startswith('_'):
            continue
        if attribute.key == column_db_name:
            return attribute_name
    return None


def is_sqlalchemy_polymorphic(cls):
    return hasattr(cls, '__mapper_args__') and cls.__mapper_args__.get('polymorphic_on') is not None


class PolymorphicModelSerializer(ModelSerializer):
    """
    Serializer for models that have a common base class. Can be used as serializer for endpoints that have objects
    from different classes (but have a common base)
    """

    def __init__(self, declarative_class):
        super().__init__(declarative_class)

        if is_sqlalchemy_polymorphic(declarative_class):
            self.is_polymorphic = True
            self.sub_serializers = self._get_sub_serializers(declarative_class)
            self.identity_key = _get_identity_key(declarative_class)
        else:
            self.is_polymorphic = False

    @classmethod
    def _get_sub_serializers(cls, declarative_class):

        serializers_sub_class_map = {
            sub_cls.get_identity(): sub_cls for sub_cls in cls.__subclasses__() if sub_cls.get_identity()
        }

        return {
            _get_identity(sub_cls): serializers_sub_class_map.get(_get_identity(sub_cls), cls)(sub_cls)
            for sub_cls in declarative_class.__subclasses__()
        }

    @classmethod
    def get_identity(cls):
        return _get_identity(cls.__model_class__) if hasattr(cls, '__model_class__') else None

    def load(self, serialized, existing_model=None, session=None):
        if self.is_polymorphic:
            model_identity = serialized.get(self.identity_key)
            if model_identity and self.sub_serializers.get(model_identity):
                return self.sub_serializers[model_identity].load(serialized, existing_model, session)
        return super().load(serialized, existing_model, session)

    def dump(self, model):
        if self.is_polymorphic:
            model_identity = _get_identity(model)
            if model_identity in self.sub_serializers:
                return self.sub_serializers[model_identity].dump(model)
        return super().dump(model)

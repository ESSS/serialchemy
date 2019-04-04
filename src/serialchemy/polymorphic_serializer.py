from sqlalchemy import Column
from sqlalchemy.orm import class_mapper

from serialchemy import ModelSerializer


def class_identity(cls):
    return cls.__mapper_args__['polymorphic_identity']


def class_identity_key(cls):
    identity_column = cls.__mapper_args__['polymorphic_on']
    assert isinstance(identity_column, Column)

    for prop in class_mapper(cls).iterate_properties:
        if hasattr(prop, 'columns') and prop.columns[0].key == identity_column.key:
            class_identity_key = prop.key
            break
    else:
        class_identity_key = identity_column.key

    return class_identity_key


class PolymorphicModelSerializer(ModelSerializer):
    """
    Serializer for models that have a common base class. Can be used as serializer for objects
    from different classes (but have a common base)
    """

    def __init__(self, declarative_class, base_model_serializer=None):
        super().__init__(declarative_class)

        if base_model_serializer:
            assert issubclass(base_model_serializer, ModelSerializer), \
                f'Invalid base model serializer: {base_model_serializer}. Should be subclass of ModelSerializer.'
        base_model_serializer = base_model_serializer or ModelSerializer

        self.sub_serializers = {class_identity(cls): base_model_serializer(cls) for cls in declarative_class.__subclasses__()}
        self.identity_key = class_identity_key(declarative_class)

    def load(self, serialized, existing_model=None, session=None):
        model_identity = serialized.get(self.identity_key, None)
        if model_identity and self.sub_serializers.get(model_identity, None):
            return self.sub_serializers[model_identity].load(serialized, existing_model, session)
        return super().load(serialized, existing_model, session)

    def dump(self, model):
        model_identity = class_identity(model)
        if model_identity in self.sub_serializers:
            return self.sub_serializers[model_identity].dump(model)
        return super().dump(model)

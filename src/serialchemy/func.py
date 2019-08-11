from serialchemy import ModelSerializer


def dump(model, nest_foreign_keys=False):
    """
    Serialize a SQLAlchemy model.

    :param model: the SQLAlchemy model instance
    :type model: sqlalchemy.ext.declarative.DeclarativeMeta

    :param bool nest_foreign_keys: If True, serialize any foreign key column as a nested object.

    :rtype: dict
    """
    serializer = ModelSerializer(model.__class__, nest_foreign_keys=nest_foreign_keys)
    return serializer.dump(model)


def load(serialized, model_class, nest_foreign_keys=False):
    """
    Deserialize a dict into a SQLAlchemy model.

    :param dict serialized: the serialized object.

    :param model_class: the SQLAlchemy model class.
    :type model_class: Type[sqlalchemy.ext.declarative.DeclarativeMeta]

    :param bool nest_foreign_keys: If True, serialized content has foreign keys as nested object.

    :rtype: model_class
    """
    serializer = ModelSerializer(model_class, nest_foreign_keys=nest_foreign_keys)
    return serializer.load(serialized)

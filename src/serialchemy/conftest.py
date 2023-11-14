from typing import Literal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

MappingType = Literal['imperative', 'declarative']


@pytest.fixture()
def engine():
    engine = create_engine('sqlite:///:memory:')
    return engine


def get_metadata(mapping_type):
    if mapping_type == 'imperative':
        from serialchemy._tests.sample_model_imperative.orm_mapping import mapper_registry

        return mapper_registry.metadata
    else:
        from serialchemy._tests.sample_model import Base

        return Base.metadata


@pytest.fixture(params=['imperative', 'declarative'])
def mapping_type(request) -> MappingType:
    return request.param


@pytest.fixture()
def model(mapping_type: MappingType):
    if mapping_type == 'imperative':
        from serialchemy._tests.sample_model_imperative import model

        get_metadata(mapping_type)  # apply mapping
        return model
    else:
        from serialchemy._tests import sample_model

        return sample_model


@pytest.fixture()
def db_session(mapping_type: MappingType, engine):
    metadata = get_metadata(mapping_type)
    metadata.drop_all(engine)
    metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session

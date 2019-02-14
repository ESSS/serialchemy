import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from serialchemy._tests.sample_model import Base


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session

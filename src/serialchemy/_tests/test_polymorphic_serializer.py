from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from serialchemy import PolymorphicModelSerializer


def test_polymorphic_pure_enum_identity_handling(db_session):
    Base = declarative_base()

    class TestEnum(Enum):
        TYPE_A = "type_a"
        TYPE_B = "type_b"

    class BaseTest(Base):
        __tablename__ = "base_test"
        id = Column(Integer, primary_key=True)
        type = Column(String)

        __mapper_args__ = {
            "polymorphic_on": type,
            "polymorphic_identity": None,
        }

    class TestA(BaseTest):
        __tablename__ = "test_a"
        id = Column(Integer, ForeignKey("base_test.id"), primary_key=True)

        __mapper_args__ = {
            "polymorphic_identity": TestEnum.TYPE_A,  # Pure enum
        }

    Base.metadata.create_all(db_session.bind)

    obj = TestA(type=TestEnum.TYPE_A.value)
    db_session.add(obj)
    db_session.commit()

    serializer = PolymorphicModelSerializer(BaseTest)
    serialized_obj = serializer.dump(obj)

    # Verify that the serialized value is the .value of the enum (not the Enum itself)
    assert serialized_obj["type"] == TestEnum.TYPE_A.value

    loaded_obj = serializer.load(serialized_obj, session=db_session)
    assert isinstance(loaded_obj, TestA)
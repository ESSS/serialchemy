from abc import ABC, abstractmethod


class Serializer(ABC):
    @abstractmethod
    def dump(self, value):
        pass

    @abstractmethod
    def load(self, serialized, **kw):
        pass


class ColumnSerializer(Serializer):
    def __init__(self, column):
        self.column = column

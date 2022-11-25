from serialchemy import Field, Serializer


class CustomSerializer(Serializer):
    def dump(self, value):
        return f'dumped {value}'

    def load(self, serialized, **kw):
        return f'loaded {serialized}'


def test_field_serializer_is_called_for_falsy_values():
    field = Field()
    assert field.dump('') == ''
    assert field.load('') == ''

    custom_field = Field(serializer=CustomSerializer())
    assert custom_field.dump('') == 'dumped '
    assert custom_field.load('') == 'loaded '

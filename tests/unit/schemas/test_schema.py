from jsonschema import Draft7Validator

from jina.schemas import get_full_schema


def test_full_schema():
    schema = get_full_schema()
    Draft7Validator.check_schema(schema)
    # assert jina concepts exist in definitions
    for concept in ['gateway', 'flow', 'metas', 'deployment']:
        assert f'Jina::{concept.capitalize()}' in schema['definitions']

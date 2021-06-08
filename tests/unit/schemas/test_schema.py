from jsonschema import Draft7Validator

from jina.schemas import get_full_schema


def test_full_schema():
    Draft7Validator.check_schema(get_full_schema())

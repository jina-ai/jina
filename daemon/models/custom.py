import argparse
from typing import Iterable, Callable

from pydantic import create_model, validator, Field, BaseConfig

from cli.export import _export_parser_args
from jina.helper import typename, random_identity
from jina import helper


def _get_validator(field: str, choices: Iterable):
    """ Pydantic validator classmethod generator to validate fields exist in choices """

    def validate_arg_choices(v, values):
        if v not in choices:
            raise ValueError(
                f'Invalid value {v}({typename(v)} for field {field}. '
                f'Valid choices are {choices}'
            )
        return v

    validate_arg_choices.__qualname__ = 'validate_' + field
    return validator(field, allow_reuse=True)(validate_arg_choices)


def _get_pydantic_fields(parser: Callable[..., 'argparse.ArgumentParser']):
    all_options = {}
    choices_validators = {}

    for a in _export_parser_args(parser):
        if a.get('choices', None):
            choices_validators[f'validator_for_{a["name"]}'] = _get_validator(
                field=a['name'], choices=set(a['choices'])
            )
        if a['required']:
            f = Field(default=..., example=a['default'], description=a['help'])
        elif a.get('default_factory', None):
            if a['default_factory'] == random_identity.__name__:
                f = Field(
                    default_factory=random_identity,
                    example=a['default'],
                    description=a['help'],
                )
            elif a['default_factory'] == helper.random_port.__name__:
                f = Field(
                    default_factory=helper.random_port,
                    example=a['default'],
                    description=a['help'],
                )
            else:
                raise ValueError(
                    f'default_factory: {a["default_factory"]} is not recognizable for {a}'
                )
        else:
            f = Field(default=a['default'], description=a['help'])

        all_options[a['name']] = (a['type'], f)

    return all_options, choices_validators


def build_pydantic_model(model_name: str, module: str):
    class _PydanticConfig(BaseConfig):
        arbitrary_types_allowed = True

    from jina.parsers import helper

    helper._SHOW_ALL_ARGS, old_val = True, helper._SHOW_ALL_ARGS
    from jina.parsers import set_pea_parser, set_pod_parser
    from jina.parsers.flow import set_flow_parser

    if module == 'pod':
        parser = set_pod_parser
    elif module == 'pea':
        parser = set_pea_parser
    elif module == 'flow':
        parser = set_flow_parser
    else:
        raise TypeError(f'{module} is not supported')

    all_fields, field_validators = _get_pydantic_fields(parser)

    helper._SHOW_ALL_ARGS = old_val
    return create_model(
        model_name,
        **all_fields,
        __config__=_PydanticConfig,
        __validators__=field_validators,
    )

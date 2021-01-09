import argparse
from typing import Union

import requests
from pydantic import create_model, validator, Field

JINA_API_URL = 'https://api.jina.ai/latest'


def get_latest_api():
    """Fetches the latest jina cli args"""
    response = requests.get(JINA_API_URL)
    all_cli_args = response.json()
    return all_cli_args


def get_module_args(all_args: list, module: str):
    """Fetches the cli args for modules like `flow`, `pod`"""
    for current_module in all_args['methods']:
        if current_module['name'] == module:
            module_args = current_module
            return module_args


def generate_validator(field: str, choices: list):
    """ Pydantic validator classmethod generator to validate fields exist in choices """

    def validate_arg_choices(v, values):
        if v not in choices:
            raise ValueError(f'Invalid value {v} for field {field}'
                             f'Valid choices are {choices}')
        return v

    validate_arg_choices.__qualname__ = 'validate_' + field
    return validator(field, allow_reuse=True)(validate_arg_choices)


def get_pydantic_fields(config: Union[dict, argparse.ArgumentParser]):
    all_options = {}
    choices_validators = {}

    if isinstance(config, dict):
        for arg in config['options']:
            arg_key = arg['name']
            arg_type = arg['type']
            if arg['choices']:
                choices_validators[f'validator_for_{arg_key}'] = generate_validator(field=arg_key,
                                                                                    choices=arg['choices'])
            if arg_type == 'method':
                arg_type = type(arg['default']) if arg['default'] else int
            arg_type = 'str' if arg_type == 'FileType' else arg_type

            current_field = Field(default=arg['default'],
                                  example=arg['default'],
                                  description=arg['help'])
            all_options[arg_key] = (arg_type, current_field)

    # Issue: For all args that have a default value which comes from a function call (get_random_identity() or random_port()),
    # 1st pydantic model invocation sets these default values, means build_pydantic_model(...) sets the args, not SinglePodModel()
    # In case of multiple Pods, port conflict happens because of same port set as default in both.
    # TODO(Deepankar): Add support for `default_factory` for default args that are functions
    if isinstance(config, argparse.ArgumentParser):
        # Ignoring first 3 as they're generic args
        from jina.parsers.helper import KVAppendAction
        for arg in config._actions[3:]:
            arg_key = arg.dest
            arg_type = arg.type
            if arg.choices:
                choices_validators[f'validator_for_{arg_key}'] = generate_validator(field=arg_key,
                                                                                    choices=arg.choices)
            # This is to handle the Enum args (to check if it is a bound method)
            if hasattr(arg_type, '__self__'):
                arg_type = type(arg.default) if arg.default else int
            arg_type = str if isinstance(arg_type, argparse.FileType) else arg_type
            arg_type = dict if type(arg) == KVAppendAction else arg_type

            current_field = Field(default=arg.default,
                                  example=arg.default,
                                  description=arg.help)
            all_options[arg_key] = (arg_type, current_field)

    return all_options, choices_validators


class PydanticConfig:
    arbitrary_types_allowed = True


def build_pydantic_model(kind: str = 'local',
                         model_name: str = 'CustomModel',
                         module: str = 'pod'):
    if kind == 'api':
        all_cli_args = get_latest_api()
        module_args = get_module_args(all_args=all_cli_args,
                                      module=module)
        all_fields, field_validators = get_pydantic_fields(config=module_args)

    elif kind == 'local':
        from jina.parsers import set_pea_parser, set_pod_parser
        from jina.parsers.flow import set_flow_parser
        if module == 'pod':
            parser = set_pod_parser()
        elif module == 'pea':
            parser = set_pea_parser()
        elif module == 'flow':
            parser = set_flow_parser()
        all_fields, field_validators = get_pydantic_fields(config=parser)

    return create_model(model_name,
                        **all_fields,
                        __config__=PydanticConfig,
                        __validators__=field_validators)

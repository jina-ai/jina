import os
import re

from typing import List, Dict
from jina.excepts import InvalidSecrets


class JinaSecret:

    def __init__(self, name: str, key: str, type: str, *args, **kwargs):
        assert type in ['env'], f'type {type} is not a valid type, it must be one of ["env"]'
        self.key = key
        self.name = name
        self.type = type


secrets_regex_str = r'\${{\s?SECRETS\.[a-zA-Z0-9_]*\s?}}|\${{\s?secrets\.[a-zA-Z0-9_]*\s?}}'
secret_name_regex_str = r'\.(.*?)(\s|\})'
secrets_regex = re.compile(
    secrets_regex_str
)  # matches expressions of form '${{ SECRETS.var }}' or '${{ secrets.var }}'
secrets_name_regex = re.compile(secret_name_regex_str)


def replace_args_with_secrets(args, secrets: List[Dict]):
    if secrets is None:
        return args
    secrets_obj = []
    for secret in secrets:
        try:
            s_obj = JinaSecret(**secret)
            secrets_obj.append(s_obj)
        except TypeError:
            raise InvalidSecrets(f'Secret {secret} passed is not a valid secret object')
        except AssertionError as e:
            raise InvalidSecrets(f'{e.args}')

    def replace_recursive(b):
        for k, v in b.items():
            if type(v) == str:
                match = re.search(secrets_regex, v)
                if match is not None:
                    matched_str = v[match.span()[0]: match.span()[1]]

                    name_match = re.search(secrets_name_regex, matched_str)
                    secret_name = matched_str[name_match.span()[0]: name_match.span()[1]][1:][:-1]

                    for secret in secrets_obj:
                        if secret.name == secret_name or (secret.type == 'env' and secret.key == secret_name):
                            secret_value = os.environ[secret.key]
                            out = re.sub(secrets_regex_str, secret_value, v)
                            b[k] = out
            if type(v) == dict:
                replace_recursive(v)

    d = vars(args)
    replace_recursive(d)

    return args

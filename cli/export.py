__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import os


def api_to_dict():
    from jina import __version__
    from jina.parsers import get_main_parser

    parsers = get_main_parser()._actions[-1].choices

    all_d = {'name': 'Jina',
             'description': 'Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep '
                            'learning technology',
             'license': 'Apache 2.0',
             'vendor': 'Jina AI Limited',
             'source': 'https://github.com/jina-ai/jina/tree/' + os.environ.get('JINA_VCS_VERSION', 'master'),
             'url': 'https://jina.ai',
             'docs': 'https://docs.jina.ai',
             'authors': 'dev-team@jina.ai',
             'version': __version__,
             'methods': [],
             'revision': os.environ.get('JINA_VCS_VERSION')}

    for p_name in parsers.keys():
        d = {'name': p_name, 'options': []}
        for ddd in _export_parser_args(lambda *x: get_main_parser()._actions[-1].choices[p_name], type_as_str=True):
            d['options'].append(ddd)
        all_d['methods'].append(d)

    return all_d


def _export_parser_args(parser_fn, type_as_str: bool = False):
    from jina.enums import BetterEnum
    from argparse import _StoreAction, _StoreTrueAction

    port_attr = ('help', 'choices', 'default', 'required', 'option_strings', 'dest')
    parser = parser_fn()
    parser2 = parser_fn()
    random_dest = set()
    for a, b in zip(parser._actions, parser2._actions):
        if a.default != b.default:
            random_dest.add(a.dest)
    for a in parser._actions:
        if isinstance(a, (_StoreAction, _StoreTrueAction)) and a.help != argparse.SUPPRESS:
            ddd = {p: getattr(a, p) for p in port_attr}
            if isinstance(a, _StoreTrueAction):
                ddd['type'] = bool
            else:
                ddd['type'] = a.type
            if ddd['choices']:
                ddd['choices'] = [str(k) if isinstance(k, BetterEnum) else k for k in ddd['choices']]
                ddd['type'] = str
            if isinstance(ddd['default'], BetterEnum):
                ddd['default'] = str(ddd['default'])
                ddd['type'] = str
            if a.dest in random_dest:
                ddd['default_random'] = True
                from jina.helper import random_identity, random_port
                if isinstance(a.default, str):
                    ddd['default_factory'] = random_identity.__name__
                elif isinstance(a.default, int):
                    ddd['default_factory'] = random_port.__name__
            else:
                ddd['default_random'] = False
            if type_as_str:
                ddd['type'] = ddd['type'].__name__
            ddd['name'] = ddd.pop('dest')
            yield ddd

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os


def api_to_dict():
    from ..enums import BetterEnum
    from .. import __version__
    from .parser import get_main_parser

    from argparse import _StoreAction, _StoreTrueAction
    port_attr = ('help', 'choices', 'default', 'required', 'option_strings', 'dest')

    parsers = get_main_parser()._actions[-1].choices

    all_d = {'name': 'Jina',
             'description': 'Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology',
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
        parser = get_main_parser()._actions[-1].choices[p_name]
        parser2 = get_main_parser()._actions[-1].choices[p_name]
        random_dest = set()
        for a, b in zip(parser._actions, parser2._actions):
            if a.default != b.default:
                random_dest.add(a.dest)
        for a in parser._actions:
            if isinstance(a, _StoreAction) or isinstance(a, _StoreTrueAction):
                ddd = {p: getattr(a, p) for p in port_attr}
                if a.type:
                    ddd['type'] = a.type.__name__ if isinstance(a.type, type) else type(a.type).__name__
                elif isinstance(a, _StoreTrueAction):
                    ddd['type'] = 'bool'
                else:
                    ddd['type'] = a.type
                if ddd['choices']:
                    ddd['choices'] = [str(k) if isinstance(k, BetterEnum) else k for k in ddd['choices']]
                if isinstance(ddd['default'], BetterEnum):
                    ddd['default'] = str(ddd['default'])
                if a.dest in random_dest:
                    ddd['default_random'] = True
                else:
                    ddd['default_random'] = False
                ddd['name'] = ddd.pop('dest')

                d['options'].append(ddd)
        all_d['methods'].append(d)
    return all_d

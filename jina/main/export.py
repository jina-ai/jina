__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os


def api_to_dict():
    from ..enums import BetterEnum
    from .. import __version__
    from .parser import set_pod_parser, set_pea_parser, \
        set_flow_parser, set_client_cli_parser, \
        set_gateway_parser, set_hw_parser, set_ping_parser, set_check_parser, set_export_api_parser
    from argparse import _StoreAction, _StoreTrueAction
    port_attr = ('help', 'choices', 'default', 'required', 'option_strings', 'dest')

    parsers = {'pod': set_pod_parser,
               'pea': set_pea_parser,
               'flow': set_flow_parser,
               'client': set_client_cli_parser,
               'gateway': set_gateway_parser,
               'hello-world': set_hw_parser,
               'ping': set_ping_parser,
               'check': set_check_parser,
               'export-api': set_export_api_parser}

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

    for p_name, pp in parsers.items():
        d = {'name': p_name, 'options': []}
        parser = pp()
        parser2 = pp()
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

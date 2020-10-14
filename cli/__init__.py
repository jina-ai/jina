__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys


def _get_run_args(print_args: bool = True):
    from jina.logging import default_logger
    from jina.parser import get_main_parser
    from jina.helper import colored

    parser = get_main_parser()
    if len(sys.argv) > 1:
        from argparse import _StoreAction, _StoreTrueAction
        args = parser.parse_args()
        p = parser._actions[-1].choices[sys.argv[1]]
        default_args = {a.dest: a.default for a in p._actions if
                        isinstance(a, _StoreAction) or isinstance(a, _StoreTrueAction)}
        if print_args:
            from pkg_resources import resource_filename
            with open(resource_filename('jina', '/'.join(('resources', 'jina.logo')))) as fp:
                logo_str = fp.read()
            param_str = []
            for k, v in sorted(vars(args).items()):
                j = f'{k.replace("_", "-"): >30.30} = {str(v):30.30}'
                if default_args.get(k, None) == v:
                    param_str.append('   ' + j)
                else:
                    param_str.append('🔧️ ' + colored(j, 'blue', 'on_yellow'))
            param_str = '\n'.join(param_str)
            default_logger.info(f'\n{logo_str}\n▶️  {" ".join(sys.argv)}\n{param_str}\n')
        return args
    else:
        parser.print_help()
        exit()


def _quick_ac_lookup():
    from .autocomplete import ac_table
    if len(sys.argv) > 1:
        if sys.argv[1] == 'commands':
            for k in ac_table['commands']:
                print(k)
            exit()
        elif sys.argv[1] == 'completions':
            # search with the longest shared prefix
            for j in range(len(sys.argv), 2, -1):
                _input = ' '.join(sys.argv[2:j]).strip()
                if _input in ac_table['completions']:
                    compl = ac_table['completions'][_input]
                    for k in compl:
                        if k not in sys.argv:
                            print(k)
                    break
            exit()


def main():
    """The main entrypoint of the CLI """
    _quick_ac_lookup()
    from . import api
    args = _get_run_args()
    getattr(api, args.cli.replace('-', '_'))(args)

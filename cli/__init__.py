import os
import shutil
import subprocess
import sys

PLUGIN_INFO = {
    'now': {  # the subcommand your project should be reachable under, e.g. "jina now ..."
        'name': 'Jina Now',  # what your project is called
        'pip-package': 'jina-now',  # the pip package name of your project
        'internal-command': 'jina-now',  # the command of your project, e.g. Now's cli is reachable via "jina-now ..."
    }
}


def _get_run_args(print_args: bool = True):
    from jina.helper import get_rich_console
    from jina.parsers import get_main_parser

    console = get_rich_console()

    silent_print = {'help', 'hub'}

    parser = get_main_parser()
    if len(sys.argv) > 1:
        from argparse import _StoreAction, _StoreTrueAction

        from rich import box
        from rich.table import Table

        args, unknown = parser.parse_known_args()

        if unknown:
            from jina.helper import warn_unknown_args

            unknown = list(filter(lambda x: x.startswith('--'), unknown))
            warn_unknown_args(unknown)

        if args.cli not in silent_print and print_args:
            from jina import __resources_path__

            p = parser._actions[-1].choices[sys.argv[1]]
            default_args = {
                a.dest: a.default
                for a in p._actions
                if isinstance(a, (_StoreAction, _StoreTrueAction))
            }

            with open(os.path.join(__resources_path__, 'jina.logo')) as fp:
                logo_str = fp.read()

            param_str = Table(title=None, box=box.ROUNDED, highlight=True)
            param_str.add_column('')
            param_str.add_column('Parameters', justify='right')
            param_str.add_column('Value', justify='left')

            for k, v in sorted(vars(args).items()):
                sign = ' ' if default_args.get(k, None) == v else '🔧️'
                param = k.replace('_', '-')
                value = str(v)

                style = None if default_args.get(k, None) == v else 'blue on yellow'

                param_str.add_row(sign, param, value, style=style)

            print(f'\n{logo_str}\n')
            console.print(f'▶️  {" ".join(sys.argv)}', param_str)
        return args
    else:
        parser.print_help()
        exit()


def _quick_ac_lookup():
    from cli.autocomplete import ac_table

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


def _is_latest_version(suppress_on_error=True):
    try:
        import json
        import warnings
        from urllib.request import Request, urlopen

        from jina import __version__

        req = Request(
            'https://api.jina.ai/latest', headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urlopen(
            req, timeout=5
        ) as resp:  # 'with' is important to close the resource after use
            latest_ver = json.load(resp)['version']
            from packaging.version import Version

            latest_ver = Version(latest_ver)
            cur_ver = Version(__version__)
            if cur_ver < latest_ver:
                from jina.logging.predefined import default_logger

                default_logger.warning(
                    f'You are using Jina version {cur_ver}, however version {latest_ver} is available. '
                    f'You should consider upgrading via the "pip install --upgrade jina" command.'
                )
                return False
        return True
    except:
        # no network, two slow, api.jina.ai is down
        if not suppress_on_error:
            raise


def _try_plugin_command():
    """Tries to call the CLI of an external Jina project."""
    argv = sys.argv
    if len(argv) < 2:
        return False

    def _cmd_exists(cmd):
        return shutil.which(cmd) is not None

    subcommand = argv[1]
    cmd = (
        PLUGIN_INFO[subcommand]['internal-command']
        if subcommand in PLUGIN_INFO
        else 'jina-' + subcommand
    )
    if _cmd_exists(cmd):
        subprocess.run([cmd] + argv[2:])
        return True

    if subcommand in PLUGIN_INFO:
        from jina.helper import get_rich_console

        cmd_info = PLUGIN_INFO[subcommand]
        project, package = cmd_info['name'], cmd_info['pip-package']
        console = get_rich_console()
        console.print(
            f"It seems like [yellow]{project}[/yellow] is not installed in your environment. To use it via the [green]'jina {subcommand}'[/green] command, install it first: [green]'pip install {package}'[/green]."
        )
        return True
    return False


def main():
    """The main entrypoint of the CLI"""

    # checking version info in another thread
    import threading

    threading.Thread(target=_is_latest_version, daemon=True).start()

    found_plugin = _try_plugin_command()

    if not found_plugin:
        _quick_ac_lookup()

        from cli import api

        args = _get_run_args()

        getattr(api, args.cli.replace('-', '_'))(args)

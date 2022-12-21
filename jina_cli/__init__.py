import os
import shutil
import subprocess
import sys


def _get_run_args(print_args: bool = True):
    from jina.helper import get_rich_console
    from jina.parsers import get_main_parser

    console = get_rich_console()

    silent_print = {'help', 'hub', 'export', 'auth', 'cloud', 'ping'}

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
            from jina.constants import __resources_path__

            p = parser._actions[-1].choices[sys.argv[1]]
            default_args = {
                a.dest: a.default
                for a in p._actions
                if isinstance(a, (_StoreAction, _StoreTrueAction))
            }

            with open(os.path.join(__resources_path__, 'jina.logo')) as fp:
                logo_str = fp.read()

            param_str = Table(
                title=' '.join(sys.argv),
                box=box.ROUNDED,
                highlight=True,
                title_justify='left',
            )
            param_str.add_column('Argument', justify='right')
            param_str.add_column('Value', justify='left')

            for k, v in sorted(vars(args).items()):
                param = k.replace('_', '-')
                value = str(v)

                if not default_args.get(k, None) == v:
                    value = f'[b]{value}[/]'

                param_str.add_row(param, value)

            if 'JINA_LOG_NO_COLOR' not in os.environ:
                print(f'\n{logo_str}\n')
            console.print(param_str)
        return args
    else:
        parser.print_help()
        exit()


def _quick_ac_lookup():
    from jina_cli.autocomplete import ac_table

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


def _try_plugin_command():
    """Tries to call the CLI of an external Jina project.

    :return: if the plugin has been found (locally or among the known plugins)
    """
    argv = sys.argv
    if len(argv) < 2:  # no command given
        return False

    from jina_cli.autocomplete import ac_table

    if argv[1] in ac_table['commands']:  # native command can't be plugin command
        return False

    def _cmd_exists(cmd):
        return shutil.which(cmd) is not None

    subcommand = argv[1]
    cmd = 'jina-' + subcommand
    if _cmd_exists(cmd):
        subprocess.run([cmd] + argv[2:])
        return True

    from jina_cli.known_plugins import plugin_info

    if subcommand in plugin_info:
        from jina.helper import get_rich_console

        cmd_info = plugin_info[subcommand]
        project, package = cmd_info['display-name'], cmd_info['pip-package']
        console = get_rich_console()
        console.print(
            f"It seems like [yellow]{project}[/yellow] is not installed in your environment."
            f"To use it via the [green]'jina {subcommand}'[/green] command, "
            f"install it first: [green]'pip install {package}'[/green]."
        )
        return True
    return False


def main():
    """The main entrypoint of the CLI"""

    found_plugin = _try_plugin_command()

    if not found_plugin:
        _quick_ac_lookup()

        from jina_cli import api

        args = _get_run_args()

        getattr(api, args.cli.replace('-', '_'))(args)

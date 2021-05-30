import os

from . import __jina_env__
from .helper import colored
from .importer import import_classes, _print_dep_tree_rst
from .logging.predefined import default_logger

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class ImportChecker:
    """Check all executors, drivers and handler functions in the package."""

    def __init__(self, args: 'argparse.Namespace'):
        """
        Create a new :class:`ImportChecker`.

        :param args: args provided by the CLI.
        """
        default_logger.info('\navailable core executors\n'.upper())

        _r = import_classes('jina.executors', show_import_table=True, import_once=False)

        if args.summary_exec:
            with open(args.summary_exec, 'w') as fp:
                _print_dep_tree_rst(fp, _r, 'Executor')

        default_logger.info('\navailable hub executors\n'.upper())

        _r = import_classes('jina.hub', show_import_table=True, import_once=False)

        if args.summary_exec and _r:
            with open(args.summary_exec, 'w') as fp:
                _print_dep_tree_rst(fp, _r, 'Executor')

        default_logger.info('\nenvironment variables\n'.upper())
        default_logger.info(
            '\n'.join(
                f'{k:<20}\t{os.environ.get(k, colored("(unset)", "yellow"))}'
                for k in __jina_env__
            )
        )


class NetworkChecker:
    """Check if a BasePod is running or not."""

    def __init__(self, args: 'argparse.Namespace'):
        """
        Create a new :class:`NetworkChecker`.

        :param args: args provided by the CLI.
        """
        from .peapods.zmq import send_ctrl_message
        from .logging.profile import TimeContext
        from google.protobuf.json_format import MessageToJson
        import time

        ctrl_addr = f'tcp://{args.host}:{args.port}'
        try:
            total_time = 0
            total_success = 0
            for j in range(args.retries):
                with TimeContext(
                    f'ping {ctrl_addr} at {j} round', default_logger
                ) as tc:
                    r = send_ctrl_message(ctrl_addr, 'STATUS', timeout=args.timeout)
                    if not r:
                        default_logger.warning(
                            'not responding, retry (%d/%d) in 1s'
                            % (j + 1, args.retries)
                        )
                    else:
                        total_success += 1
                        if args.print_response:
                            default_logger.info(f'returns {MessageToJson(r.proto)}')
                total_time += tc.duration
                time.sleep(1)
            if total_success < args.retries:
                default_logger.warning(
                    'message lost %.0f%% (%d/%d) '
                    % (
                        (1 - total_success / args.retries) * 100,
                        args.retries - total_success,
                        args.retries,
                    )
                )
            if total_success > 0:
                default_logger.success(
                    'avg. latency: %.0f ms' % (total_time / total_success * 1000)
                )
                exit(0)
        except KeyboardInterrupt:
            pass

        # returns 1 (anomaly) when it comes to here
        exit(1)

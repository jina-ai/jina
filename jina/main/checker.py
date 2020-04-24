__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

from .. import __jina_env__, import_classes
from ..helper import colored, print_dep_tree_rst
from ..logging import default_logger

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class ImportChecker:
    """Check all executors, drivers and handler functions in the package. """

    def __init__(self, args: 'argparse.Namespace'):
        default_logger.info('\navailable executors\n'.upper())

        _r = import_classes('jina.executors', show_import_table=True, import_once=False)

        if args.summary_exec:
            with open(args.summary_exec, 'w') as fp:
                print_dep_tree_rst(fp, _r, 'Executor')

        default_logger.info('\navailable drivers\n'.upper())
        _r = import_classes('jina.drivers', show_import_table=True, import_once=False)

        if args.summary_driver:
            with open(args.summary_driver, 'w') as fp:
                print_dep_tree_rst(fp, _r, 'Driver')

        # check available driver group

        default_logger.info('\nenvironment variables\n'.upper())
        default_logger.info('\n'.join('%-20s\t%s' % (k, os.environ.get(k, colored('(unset)', 'yellow'))) for k in
                                      __jina_env__))


class NetworkChecker:
    """Check if a BasePod is running or not """

    def __init__(self, args: 'argparse.Namespace'):
        from ..peapods.pea import send_ctrl_message
        from ..proto import jina_pb2
        from ..logging.profile import TimeContext
        from google.protobuf.json_format import MessageToJson
        import time
        ctrl_addr = 'tcp://%s:%d' % (args.host, args.port)
        try:
            total_time = 0
            total_success = 0
            for j in range(args.retries):
                with TimeContext('ping %s at %d round' % (ctrl_addr, j), default_logger) as tc:
                    r = send_ctrl_message(ctrl_addr, jina_pb2.Request.ControlRequest.STATUS, timeout=args.timeout)
                    if not r:
                        default_logger.warning('not responding, retry (%d/%d) in 1s' % (j + 1, args.retries))
                    else:
                        total_success += 1
                        if args.print_response:
                            default_logger.info('returns %s' % MessageToJson(r))
                total_time += tc.duration
                time.sleep(1)
            if total_success < args.retries:
                default_logger.warning('message lost %.0f%% (%d/%d) ' % (
                    (1 - total_success / args.retries) * 100, args.retries - total_success, args.retries))
            if total_success > 0:
                default_logger.success('avg. latency: %.0f ms' % (total_time / total_success * 1000))
                exit(0)
        except KeyboardInterrupt:
            pass

        # returns 1 (anomaly) when it comes to here
        exit(1)

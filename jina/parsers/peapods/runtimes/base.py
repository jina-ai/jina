
def set_runtime_parser(parser=None):
    from .helper import get_random_identity
    from pkg_resources import resource_filename

    if not parser:
        parser = set_base_parser()
    gp0 = add_arg_group(parser, 'runtime basic arguments')
    gp0.add_argument('--name', type=str,
                     help='the name of this runtime, used to identify the pea/pod and its logs.')
    gp0.add_argument('--timeout-ready', type=int, default=10000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')
    gp0.add_argument('--runtime', type=str, choices=['thread', 'process'], default='process',
                     help='the parallel runtime of the pod')
    gp0.add_argument('--daemon', action='store_true', default=False,
                     help='when a process exits, it attempts to terminate all of its daemonic child processes. '
                          'setting it to true basically tell the context manager do not wait on this Pea')
    gp0.add_argument('--env', action=KVAppendAction,
                     metavar='KEY=VALUE', nargs='*',
                     help='a map of environment variables that are available inside runtime.')
    gp0.add_argument('--log-config', type=str,
                     default=resource_filename('jina',
                                               '/'.join(('resources', 'logging.default.yml'))),
                     help='the yaml config of the logger. note the executor inside will inherit this log config')
    gp0.add_argument('--log-id', type=str, default=get_random_identity(),
                     help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)







from jina.parsers.base import set_base_parser
from jina.parsers.helper import add_arg_group


def set_container_runtime_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, 'Container runtime arguments')

    gp0.add_argument('--uses-internal', type=str, default='BaseExecutor',
                     help='The executor config that is passed to the docker image if a docker image is used in uses. '
                          'It cannot be another docker image ')
    gp0.add_argument('--entrypoint', type=str,
                     help='the entrypoint command overrides the ENTRYPOINT in docker image. '
                          'when not set then the docker image ENTRYPOINT takes effective.')
    gp0.add_argument('--pull-latest', action='store_true', default=False,
                     help='pull the latest image before running')
    gp0.add_argument('--volumes', type=str, nargs='*', metavar='DIR',
                     help='the path on the host to be mounted inside the container. '
                          'they will be mounted to the root path, i.e. /user/test/my-workspace will be mounted to '
                          '/my-workspace inside the container. all volumes are mounted with read-write mode.')

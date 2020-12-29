from ...helper import add_arg_group


def mixin_container_runtime_parser(parser):
    """Mixing in arguments required by :class:`ContainerRuntime` into the given parser."""

    gp = add_arg_group(parser, title='ContainerRuntime')

    gp.add_argument('--uses-internal', type=str, default='BaseExecutor',
                    help='The executor config that is passed to the docker image if a docker image is used in uses. '
                         'It cannot be another docker image ')
    gp.add_argument('--entrypoint', type=str,
                    help='the entrypoint command overrides the ENTRYPOINT in docker image. '
                         'when not set then the docker image ENTRYPOINT takes effective.')
    gp.add_argument('--pull-latest', action='store_true', default=False,
                    help='pull the latest image before running')
    gp.add_argument('--volumes', type=str, nargs='*', metavar='DIR',
                    help='the path on the host to be mounted inside the container. '
                         'they will be mounted to the root path, i.e. /user/test/my-workspace will be mounted to '
                         '/my-workspace inside the container. all volumes are mounted with read-write mode.')

from ...helper import add_arg_group, DockerKwargsAppendAction


def mixin_container_runtime_parser(parser):
    """Mixing in arguments required by :class:`ContainerRuntime` into the given parser."""
    gp = add_arg_group(parser, title='ContainerRuntime')

    gp.add_argument('--uses-internal', type=str, default='BaseExecutor',
                    help='The executor config that is passed to the docker image if a docker image is used in uses. '
                         'It cannot be another docker image ')
    gp.add_argument('--entrypoint', type=str,
                    help='the entrypoint command overrides the ENTRYPOINT in docker image. '
                         'when not set then the docker image ENTRYPOINT takes effective.')
    gp.add_argument('--docker-kwargs', action=DockerKwargsAppendAction,
                    metavar='KEY:VALUE', nargs='*',
                    help='dictionary of kwargs arguments that will be passed to docker sdk when starting the docker '
                         'image. Some of the arguments can be found in docker sdk documentation ('
                         'https://docker-py.readthedocs.io/en/stable/)')
    gp.add_argument('--pull-latest', action='store_true', default=False,
                    help='pull the latest image before running')
    gp.add_argument('--volumes', type=str, nargs='*', metavar='DIR',
                    help='the path on the host to be mounted inside the container. '
                         'if separated by ":" the first part will be considered as the local host path and the second '
                         'part is the path in the container system. '
                         'If no split provided, then the basename of that directory will be mounted into container\'s '
                         'root path, e.g. --volumes="/user/test/my-workspace" '
                         'will be mounted into "/my-workspace" inside the container. all volumes are mounted with '
                         'read-write mode.')

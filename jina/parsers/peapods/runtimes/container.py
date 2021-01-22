from ...helper import add_arg_group, DockerKwargsAppendAction


def mixin_container_runtime_parser(parser):
    """Mixing in arguments required by :class:`ContainerRuntime` into the given parser."""
    gp = add_arg_group(parser, title='ContainerRuntime')

    gp.add_argument('--uses-internal', type=str, default='BaseExecutor',
                    help='''
The config runs inside the Docker container. 

Syntax and function are the same as `--uses`. This is designed when `--uses="docker://..."` this config is passed to 
the Docker container.
''')
    gp.add_argument('--entrypoint', type=str,
                    help='The entrypoint command overrides the ENTRYPOINT in Docker image. '
                         'when not set then the Docker image ENTRYPOINT takes effective.')
    gp.add_argument('--docker-kwargs', action=DockerKwargsAppendAction,
                    metavar='KEY:VALUE', nargs='*',
                    help='''
Dictionary of kwargs arguments that will be passed to Docker sdk when starting the docker '
container. 

More details can be found in the Docker SDK docs:  https://docker-py.readthedocs.io/en/stable/

''')
    gp.add_argument('--pull-latest', action='store_true', default=False,
                    help='Pull the latest image before running')
    gp.add_argument('--volumes', type=str, nargs='*', metavar='DIR',
                    help='''
The path on the host to be mounted inside the container. 

Note, 
- If separated by `:`, then the first part will be considered as the local host path and the second part is the path in the container system. 
- If no split provided, then the basename of that directory will be mounted into container's root path, e.g. `--volumes="/user/test/my-workspace"` will be mounted into "/my-workspace" inside the container. 
- All volumes are mounted with read-write mode.
''')

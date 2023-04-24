"""Argparser module for container runtimes"""
import argparse

from jina.enums import DockerNetworkMode
from jina.parsers.helper import _SHOW_ALL_ARGS, KVAppendAction, add_arg_group


def mixin_container_runtime_parser(parser, pod_type: str = 'executor'):
    """Mixing in arguments required by :class:`ContainerRuntime` into the given parser.
    :param parser: the parser instance to which we add arguments
    :param pod_type: the pod_type configured by the parser. Can be either 'executor' for an Executor pod or 'gateway' for a Gateway pod
    """
    gp = add_arg_group(parser, title='ContainerRuntime')

    gp.add_argument(
        '--entrypoint',
        type=str,
        help='The entrypoint command overrides the ENTRYPOINT in Docker image. '
        'when not set then the Docker image ENTRYPOINT takes effective.',
    )
    gp.add_argument(
        '--docker-kwargs',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
Dictionary of kwargs arguments that will be passed to Docker SDK when starting the docker '
container. 

More details can be found in the Docker SDK docs:  https://docker-py.readthedocs.io/en/stable/

''',
    )

    if pod_type == 'executor':
        gp.add_argument(
            '--volumes',
            type=str,
            nargs='*',
            metavar='DIR',
            help='''
The path on the host to be mounted inside the container. 

Note, 
- If separated by `:`, then the first part will be considered as the local host path and the second part is the path in the container system. 
- If no split provided, then the basename of that directory will be mounted into container's root path, e.g. `--volumes="/user/test/my-workspace"` will be mounted into `/my-workspace` inside the container. 
- All volumes are mounted with read-write mode.
    ''',
        )
        gp.add_argument(
            '--gpus',
            type=str,
            help=f'''
    This argument allows dockerized Jina Executors to discover local gpu devices.
    
    Note, 
    - To access all gpus, use `--gpus all`.
    - To access multiple gpus, e.g. make use of 2 gpus, use `--gpus 2`.
    - To access specified gpus based on device id, use `--gpus device=[YOUR-GPU-DEVICE-ID]`
    - To access specified gpus based on multiple device id, use `--gpus device=[YOUR-GPU-DEVICE-ID1],device=[YOUR-GPU-DEVICE-ID2]`
    - To specify more parameters, use `--gpus device=[YOUR-GPU-DEVICE-ID],runtime=nvidia,capabilities=display
        ''',
        )

        gp.add_argument(
            '--disable-auto-volume',
            action='store_true',
            default=False,
            help=f'Do not automatically mount a volume for dockerized Executors.',
        )

        gp.add_argument(
            '--force-network-mode',
            type=DockerNetworkMode.from_string,
            choices=list(DockerNetworkMode),
            default=DockerNetworkMode.AUTO,
            help=f'''
    Force the use of the specified docker network mode (default: auto). 

    Valid options are,
    - {str(DockerNetworkMode.AUTO)}: Automatically detect the docker network.
    - {str(DockerNetworkMode.HOST)}: Use the host network.
    - {str(DockerNetworkMode.BRIDGE)}: Use a user-defined bridge network.
    - {str(DockerNetworkMode.NONE)}: Use no network (equivalent to the --network=none option).
        '''
            if _SHOW_ALL_ARGS
            else argparse.SUPPRESS,
        )

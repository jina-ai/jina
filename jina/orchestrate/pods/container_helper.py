import os
import socket
from typing import TYPE_CHECKING, Optional


def get_docker_network(client) -> Optional[str]:
    """Do a best-effort guess if the caller is already in a docker network

    Check if `hostname` exists in list of docker containers.
    If a container is found, check its network id

    :param client: docker client object
    :return: network id if exists
    """
    import docker

    if TYPE_CHECKING:  # pragma: no cover
        from docker.models.containers import Container

    container: 'Container' = None
    try:
        hostname = socket.gethostname()
        container = client.containers.get(hostname)
    except docker.errors.NotFound:
        try:
            # https://stackoverflow.com/a/52988227/15683245
            with open('/proc/1/cpuset') as f:
                hostname = os.path.basename(f.read().rstrip())
            container = client.containers.get(hostname)
        except Exception:
            return None
    try:
        networks = container.attrs['NetworkSettings']['Networks']
        if networks:
            net_mode = list(networks.keys())[0]
            return networks[net_mode]['NetworkID']
        else:
            return None
    except Exception:
        return None


def get_gpu_device_requests(gpu_args):
    """Get docker device requests from gpu args

    :param gpu_args: gpu args fr
    :return: docker device requests
    """
    import docker

    _gpus = {
        'count': 0,
        'capabilities': ['gpu'],
        'device': [],
        'driver': '',
    }
    for gpu_arg in gpu_args.split(','):
        if gpu_arg == 'all':
            _gpus['count'] = -1
        if gpu_arg.isdigit():
            _gpus['count'] = int(gpu_arg)
        if '=' in gpu_arg:
            gpu_arg_key, gpu_arg_value = gpu_arg.split('=')
            if gpu_arg_key in _gpus.keys():
                if isinstance(_gpus[gpu_arg_key], list):
                    _gpus[gpu_arg_key].append(gpu_arg_value)
                else:
                    _gpus[gpu_arg_key] = gpu_arg_value
    device_requests = [
        docker.types.DeviceRequest(
            count=_gpus['count'],
            driver=_gpus['driver'],
            device_ids=_gpus['device'],
            capabilities=[_gpus['capabilities']],
        )
    ]
    return device_requests

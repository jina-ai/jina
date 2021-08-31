import os
import socket
from typing import Optional, TYPE_CHECKING


def get_docker_network(client) -> Optional[str]:
    """Do a best-effort guess if the caller is already in a docker network

    Check if `hostname` exists in list of docker containers.
    If a container is found, check its network id

    :param client: docker client object
    :return: network id if exists
    """
    import docker

    if TYPE_CHECKING:
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

import os
import sys
import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import docker

from ..dockerize import Dockerizer
from ..excepts import DockerNotFoundException


@dataclass
class Introspect:
    """ Make best effort to understand yourself """

    network: str = 'host'
    ports: Dict[str, str] = field(default_factory=dict)
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)

    @property
    def inspect(self) -> Optional[Dict]:
        """Get container id & inspect it

        :return: inspect container dict
        """
        _inspect = None
        try:
            hostname = socket.gethostname()
            _inspect = Dockerizer.raw_client.inspect_container(hostname)
        except DockerNotFoundException:
            raise
        except docker.errors.NotFound:
            try:
                with open('/proc/1/cpuset') as f:
                    hostname = os.path.basename(f.read().rstrip())
                _inspect = Dockerizer.raw_client.inspect_container(hostname)
            except Exception:
                return
        return _inspect

    def validate_volumes(self, binds: List) -> Optional[Dict]:
        """Fetch mounted volumes while starting jinad container

        :param binds: binds list from inspect
        :return: dict of mounted volumes
        """
        from .. import jinad_args, daemon_logger

        volumes = {i.split(':')[1]: i.split(':')[0] for i in binds}
        if jinad_args.workspace not in volumes:
            daemon_logger.critical(
                f'workspace {jinad_args.workspace} not mounted while starting jinad.'
                f'please start jinad container with `-v <local-directory>:{jinad_args.workspace}`'
            )
            sys.exit(-1)
        return volumes

    def __post_init__(self):
        """Get to know yourself"""
        if self.inspect:
            host_config = self.inspect['HostConfig']
            self.volumes = self.validate_volumes(host_config['Binds'])
            self.ports = host_config['PortBindings']
            self.network = host_config.get('NetworkMode', 'host')
            self.extra_hosts = host_config['ExtraHosts']

            # docker desktop adds `desktop.docker.io/wsl-distro` in Labels for WSL
            self.is_wsl = any(
                ['wsl' in i for i in self.inspect['Config']['Labels'].keys()]
            )

        """
        docker network hacks used in jinad:

        linux:
            (Recommended)
            Always start with `--net host`
            host.docker.internal:
                "not required" during jinad start (as jinad container can access all partiald ports via `net host`)
                "required" during partiald start, as it might access localhost & it is run in a custom bridge network
            port mapping:
                `--net host` doesn't support port mapping. cannot pass (& not required) `-p 8000:8000`

            (If started in a bridge network)
            Pass `--add-host host.docker.internal:host-gateway` to `docker run` command

        mac / wsl:
            `--net host` not supported. Always start with default bridge mode (no args required)
            host.docker.internal:
                "not required" during jinad start (as mac/wsl already understand it)
                "not required" during partiald start (as mac/wsl already understand it)
            port mapping:
                `-p 8000:8000` - must be passed
        """

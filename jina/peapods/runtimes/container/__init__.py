__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import asyncio
import os
import time
from pathlib import Path
from typing import Dict, Union

from jina.peapods.zmq import Zmqlet
from jina import __ready_msg__, __stop_msg__
from jina.helper import is_valid_local_config_source, kwargs2list, get_non_defaults_args
from jina.logging import JinaLogger
from jina.peapods.runtimes import BaseRuntime

__all__ = ['ContainerRuntime']


class ContainerRuntime(BaseRuntime):
    """A ContainerRuntime that will spawn a dockerized `BasePea`. It requires a docker-corresponding valid ``args.uses``

    Inside the run method, a docker container is started in the same host where this instance lives, and its logs and lifetime
    is controlled.

    """

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        import docker
        # recompute the control_addr, do not assign client, since this would be an expensive object to
        # copy in the new process generated
        client = docker.from_env()

        from sys import platform
        # Related to potential docker-in-docker communication. If `ContainerPea` lives already inside a container.
        # it will need to communicate using the `bridge` network.
        if platform in ('linux', 'linux2'):
            try:
                bridge_network = client.networks.get('bridge')
                if bridge_network:
                    self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(
                        bridge_network.attrs['IPAM']['Config'][0]['Gateway'],
                        self.args.port_ctrl,
                        self.args.ctrl_with_ipc)
            except Exception as exc:
                self.logger.warning(f'Unable to set control address from "bridge" network: {repr(exc)}'
                                    f' Control address set to {self.ctrl_addr}')
            finally:
                pass
        client.close()

    @property
    def is_idle(self) -> bool:
        raise NotImplementedError

    def _docker_run(self):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker
        client = docker.from_env()

        # the image arg should be ignored otherwise it keeps using ContainerPea in the container
        # basically all args in BasePea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        from jina.parser import set_pea_parser
        non_defaults = get_non_defaults_args(self.args, set_pea_parser(),
                                             taboo={'uses', 'entrypoint', 'volumes', 'pull_latest'})

        if self.args.pull_latest:
            self.logger.warning(f'pulling {self.args.uses}, this could take a while. if you encounter '
                                f'timeout error due to pulling takes to long, then please set '
                                f'"timeout-ready" to a larger value.')
            client.images.pull(self.args.uses)

        _volumes = {}
        if self.args.uses_internal:
            if os.path.exists(self.args.uses_internal):
                # external YAML config, need to be volumed into the container
                # uses takes value from uses_internal
                non_defaults['uses'] = '/' + os.path.basename(self.args.uses_internal)
                _volumes[os.path.abspath(self.args.uses_internal)] = {'bind': non_defaults['uses'], 'mode': 'ro'}
            elif not is_valid_local_config_source(self.args.uses_internal):
                raise FileNotFoundError(
                    f'"uses_internal" {self.args.uses_internal} is not like a path, please check it')
        if self.args.volumes:
            for p in self.args.volumes:
                Path(os.path.abspath(p)).mkdir(parents=True, exist_ok=True)
                _p = '/' + os.path.basename(p)
                _volumes[os.path.abspath(p)] = {'bind': _p, 'mode': 'rw'}

        _expose_port = [self.args.port_ctrl]
        if self.args.socket_in.is_bind:
            _expose_port.append(self.args.port_in)
        if self.args.socket_out.is_bind:
            _expose_port.append(self.args.port_out)

        from sys import platform
        if platform in ('linux', 'linux2'):
            net_mode = 'host'
        else:
            net_mode = None

        _args = kwargs2list(non_defaults)
        ports = {f'{v}/tcp': v for v in _expose_port} if not net_mode else None
        self._container = client.containers.run(self.args.uses, _args,
                                                detach=True,
                                                auto_remove=True,
                                                ports=ports,
                                                name=self.name,
                                                volumes=_volumes,
                                                network_mode=net_mode,
                                                entrypoint=self.args.entrypoint)

        # wait until the container is ready
        self.logger.info('waiting ready signal from the container')
        client.close()

    def _monitor_pea_in_container(self):
        """Direct the log from the container to local console """

        def check_ready():
            while not self.is_ready:
                time.sleep(0.1)
            self.is_ready_event.set()
            self.logger.success(__ready_msg__)
            return True

        async def _loop_body():
            import docker
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, check_ready)

            logger = JinaLogger('🐳', **vars(self.args))

            with logger:
                try:
                    for line in self._container.logs(stream=True):
                        logger.info(line.strip().decode())
                except docker.errors.NotFound:
                    self.logger.error('the container can not be started, check your arguments, entrypoint')

        asyncio.run(_loop_body())

    def run(self):
        """Start the container loop. Will spawn a docker container with a BasePea running inside.
         It will communicate with the container to see when it is ready to receive messages from the rest
         of the flow and stream the logs from the pea in the container"""
        try:
            self._docker_run()
            self._monitor_pea_in_container()
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except Exception as ex:
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            from docker.errors import NotFound
            try:
                if getattr(self, '_container'):
                    self._container.stop()
            except NotFound:
                self.logger.warning(
                    'the container is already shutdown (mostly because of some error inside the container)')
            self.unset_ready()
            self.logger.success(__stop_msg__)
            self.set_shutdown()

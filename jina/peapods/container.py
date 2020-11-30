__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import asyncio
import time
from pathlib import Path

from .pea import BasePea
from .zmq import send_ctrl_message, Zmqlet
from .. import __ready_msg__
from ..helper import is_valid_local_config_source, kwargs2list, get_non_defaults_args
from ..logging import JinaLogger


class ContainerPea(BasePea):
    """A BasePea that wraps another "dockerized" BasePea

    It requires a docker-corresponding valid ``args.uses``.
    """

    def post_init(self):
        import docker
        self._client = docker.from_env()

        # the image arg should be ignored otherwise it keeps using ContainerPea in the container
        # basically all args in BasePea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        from ..parser import set_pea_parser
        non_defaults = get_non_defaults_args(self.args, set_pea_parser(),
                                             taboo={'uses', 'entrypoint', 'volumes', 'pull_latest'})

        if self.args.pull_latest:
            self.logger.warning(f'pulling {self.args.uses}, this could take a while. if you encounter '
                                f'timeout error due to pulling takes to long, then please set '
                                f'"timeout-ready" to a larger value.')
            self._client.images.pull(self.args.uses)

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
        self._container = self._client.containers.run(self.args.uses, _args,
                                                      detach=True, auto_remove=True,
                                                      ports=ports,
                                                      name=self.name,
                                                      volumes=_volumes,
                                                      network_mode=net_mode,
                                                      entrypoint=self.args.entrypoint)

        # Related to potential docker-in-docker communication. If `ContainerPea` lives already inside a container.
        # it will need to communicate using the `bridge` network.
        if platform in ('linux', 'linux2'):
            try:
                bridge_network = self._client.networks.get('bridge')
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
        # wait until the container is ready
        self.logger.info('waiting ready signal from the container')

    def loop_body(self):
        """Direct the log from the container to local console """

        def check_ready():
            # TODO: This needs to be fixed, sleep needs to be awaited
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

    def loop_teardown(self):
        """Stop the container """
        if getattr(self, '_container', None):
            import docker
            try:
                self._container.stop()
            except docker.errors.NotFound:
                self.logger.warning(
                    'the container is already shutdown (mostly because of some error inside the container)')
        if getattr(self, '_client', None):
            self._client.close()

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        if getattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, 'STATUS',
                                     timeout=self.args.timeout_ctrl)

    @property
    def is_ready(self) -> bool:
        status = self.status
        return status and status.is_ready

    def close(self) -> None:
        self.send_terminate_signal()
        if not self.daemon:
            self.logger.close()
            self.join()

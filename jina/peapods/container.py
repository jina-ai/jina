__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from pathlib import Path

from .pea import BasePea
from .. import __ready_msg__
from ..helper import is_valid_local_config_source, kwargs2list, get_non_defaults_args
from ..logging import JinaLogger
from ..logging.queue import clear_queues


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
        if platform == "linux" or platform == "linux2":
            net_mode = 'host'
        else:
            net_mode = None

        _args = kwargs2list(non_defaults)
        self._container = self._client.containers.run(self.args.uses, _args,
                                                      detach=True, auto_remove=True,
                                                      ports={'%d/tcp' % v: v for v in
                                                             _expose_port},
                                                      name=self.name,
                                                      volumes=_volumes,
                                                      network_mode=net_mode,
                                                      entrypoint=self.args.entrypoint,
                                                      # network='mynetwork',
                                                      # publish_all_ports=True
                                                      )
        # wait until the container is ready
        self.logger.info('waiting ready signal from the container')

    def loop_body(self):
        """Direct the log from the container to local console """
        import docker

        logger = JinaLogger('🐳', **vars(self.args))
        with logger:
            try:
                for line in self._container.logs(stream=True):
                    msg = line.strip().decode()
                    # this is shabby, but it seems the only easy way to detect is_ready signal meanwhile
                    # print all error message when fails
                    if __ready_msg__ in msg:
                        self.is_ready.set()
                        self.logger.success(__ready_msg__)
                    logger.info(line.strip().decode())
            except docker.errors.NotFound:
                self.logger.error('the container can not be started, check your arguments, entrypoint')

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

    def close(self) -> None:
        self.send_terminate_signal()
        if not self.daemon:
            clear_queues()
            self.logger.close()
            self.join()

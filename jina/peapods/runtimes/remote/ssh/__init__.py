import argparse
from subprocess import Popen, PIPE

from typing import Union, Dict
from jina.peapods.runtimes.remote import BaseRemoteRuntime
from jina import __ready_msg__, __stop_msg__
from jina.helper import get_non_defaults_args, kwargs2list
from jina.logging import JinaLogger


class SSHRuntime(BaseRemoteRuntime):
    """Simple SSH based SSHRuntime for remote Pea management

    .. note::
        It requires one to upload host public key to the remote
        1. ssh-keygen -b 4096
        2. scp ~/.ssh/id_rsa.pub username@hostname:~/.ssh/authorized_keys

    .. note::
        As the terminal signal is sent via :meth:`send_terminate_signal` from
        :class:`BasePea`, there is no need to override/implement :meth:`close`
        method. Lifecycle is handled by :class:`BasePea`.
    """

    @property
    def is_idle(self) -> bool:
        raise NotImplementedError

    def __init__(self, args: Union['argparse.Namespace', Dict], kind: str):
        super().__init__(args, kind=kind)

    @property
    def pea_command(self) -> str:
        from jina.parser import set_pea_parser
        non_defaults = get_non_defaults_args(self.args, set_pea_parser(), taboo={'host'})
        _args = kwargs2list(non_defaults)
        return f'jina pea {" ".join(_args)}'

    @property
    def pod_command(self) -> str:
        from jina.parser import set_pod_parser
        non_defaults = get_non_defaults_args(self.args, set_pod_parser(), taboo={'host'})
        _args = kwargs2list(non_defaults)
        return f'jina pod {" ".join(_args)}'

    @property
    def remote_command(self) -> str:
        if self.kind == 'pea':
            return self.pea_command
        elif self.kind == 'pod':
            return self.pod_command
        else:
            raise ValueError(f'kind must be pea/pod but it is {self.kind}')

    def spawn_remote(self, ssh_proc: 'Popen') -> None:
        ssh_proc.stdin.write(self.remote_command + '\n')

    def _monitor_remote(self):
        logger = JinaLogger('🌏', **vars(self.args))
        with Popen(['ssh', self.args.host], stdout=PIPE, stdin=PIPE, bufsize=0, universal_newlines=True) as p:
            self.spawn_remote(p)
            with logger:
                for line in p.stdout:
                    msg = line.strip()
                    logger.info(msg)
                    if __ready_msg__ in msg:
                        self.is_ready_event.set()
                        self.logger.success(__ready_msg__)
                    if __stop_msg__ in msg:
                        break
            # after the pod receive TERMINATE control signal it should jump out from the loop
            p.stdin.write('logout\n')
            p.stdin.close()
            p.stdout.close()
        self.is_shutdown.set()

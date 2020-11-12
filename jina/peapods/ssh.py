from subprocess import Popen, PIPE

from .. import __ready_msg__, __stop_msg__
from ..helper import get_non_defaults_args, kwargs2list
from ..logging import JinaLogger
from ..peapods.pea import BasePea


class RemoteSSHPea(BasePea):
    """Simple SSH based RemoteSSHPea for remote Pea management

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
    def remote_command(self) -> str:
        from ..parser import set_pea_parser
        non_defaults = get_non_defaults_args(self.args, set_pea_parser(), taboo={'host'})
        _args = kwargs2list(non_defaults)
        return f'jina pea {" ".join(_args)}'

    def spawn_remote(self, ssh_proc: 'Popen') -> None:
        ssh_proc.stdin.write(self.remote_command + '\n')

    def loop_body(self):
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


class RemoteSSHPod(RemoteSSHPea):
    """SSH based pod to be used while invoking remote Pod
    """

    @property
    def remote_command(self) -> str:
        from ..parser import set_pod_parser
        non_defaults = get_non_defaults_args(self.args, set_pod_parser(), taboo={'host'})
        _args = kwargs2list(non_defaults)
        return f'jina pod {" ".join(_args)}'


class RemoteSSHMutablePod(RemoteSSHPod):
    """
    SSH based mutable pod, internally it has to maintain the context of multiple separated peas.
    Subprocess-based simple ssh session is probably no good for that, but simple ssh remotepod is
    """

    def spawn_remote(self, ssh_proc: 'Popen') -> None:
        raise NotImplementedError

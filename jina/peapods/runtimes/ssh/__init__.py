import time
from subprocess import Popen, PIPE

from ..zmq.base import ZMQManyRuntime
from ....helper import ArgNamespace


class SSHRuntime(ZMQManyRuntime):
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

    def setup(self):
        """Setup the ssh communication to host."""
        self._ssh_proc = Popen(
            ['ssh', self.args.host],
            stdout=PIPE,
            stdin=PIPE,
            bufsize=0,
            universal_newlines=True,
        )
        self._ssh_proc.stdin.write(self._pea_command + '\n')
        while self._ssh_proc.poll() is None and not self.is_ready:
            time.sleep(1)

        # two cases to reach here: 1. is_ready, 2. container is dead
        if self._ssh_proc.poll() is not None:
            raise Exception(
                'the subprocess fails to start, check the arguments or entrypoint'
            )

    def run_forever(self):
        """Method to block the main thread and print logs."""
        for line in self._ssh_proc.stdout:
            self.logger.info(line.strip())

    def teardown(self):
        """Close the ssh communication."""
        self._ssh_proc.stdin.write('logout\n')
        self._ssh_proc.stdin.close()
        self._ssh_proc.stdout.close()
        super().teardown()

    @property
    def _pea_command(self) -> str:
        from jina.parsers import set_pea_parser

        non_defaults = ArgNamespace.get_non_defaults_args(
            self.args, set_pea_parser(), taboo={'host'}
        )
        _args = ArgNamespace.kwargs2list(non_defaults)
        return f'jina pea {" ".join(_args)}'

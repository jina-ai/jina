import sys
import time
from typing import Optional

from ..helper import colored
from ..logging.profile import TimeContext


class ProgressBar(TimeContext):
    """
    A simple progress bar.

    Example:
        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop') as bar:
                do_busy()

    :param task_name: The name of the task, will be displayed in front of the bar.
    :param total_steps: Number of steps in the bar. Defaults to 100.
    :param bar_len: Total length of the bar.
    :param logger: Jina logger
    """

    def __init__(
        self,
        task_name: str,
        total_steps: float = 100.0,
        bar_len: int = 20,
        logger=None,
    ):
        super().__init__(task_name, logger)
        self.task_name = task_name
        self.total_steps = total_steps
        self.bar_len = bar_len

    @property
    def percentage_completed(self) -> float:
        """Calculate percentage complete.

        :return: the percentage of completed, [0.0, 1.0]
        """
        return self.completed / self.total_steps

    def update(self, progress: float = 1.0, total: Optional[float] = None):
        """Update progress with new values.

        :param progress: : Number of completed steps.
        :param total: Total number of steps, or ``None`` to not change. Defaults to None.
        """

        self.completed += progress
        self.total_steps = total if total is not None else self.total_steps

        sys.stdout.write('\r')
        elapsed = time.perf_counter() - self.start

        num_bars = max(1, self.percentage_completed * self.bar_len)
        num_bars = int(num_bars % self.bar_len)
        num_bars = self.bar_len if not num_bars and self.completed else max(num_bars, 1)

        sys.stdout.write(
            '{:>10} |{:<{}}| ⏱️ {:3.1f}s'.format(
                colored(self.task_name, 'cyan'),
                colored('█' * num_bars, 'green'),
                self.bar_len + 9,
                elapsed,
            )
        )
        if num_bars == self.bar_len:
            sys.stdout.write('\n')
        sys.stdout.flush()

    def __enter__(self):
        super().__enter__()
        self.completed = -1
        self.update()
        return self

    def _enter_msg(self):
        pass

    def _exit_msg(self):
        sys.stdout.write(
            f'\t{colored(f"✅ done in ⏱ {self.readable_duration}", "green")}\n'
        )

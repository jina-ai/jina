import sys
import time
from typing import Optional
from ..logging.profile import TimeContext
from ..helper import colored, get_readable_size, get_readable_time


class ProgressBar(TimeContext):
    """
    A simple progress bar.

    Example:
        .. highlight:: python
        .. code-block:: python

            with ProgressBar('loop') as bar:
                do_busy()

    :param task_name: The name of the task, will be displayed in front of the bar.
    :param total: Number of steps in the bar. Defaults to 100.
    :param bar_len: Total length of the bar.
    :param logger: Jina logger
    """

    suffix = "%(completed)d/%(total)d"
    bar_prefix = " |"
    bar_suffix = "| "
    empty_fill = " "
    fill = "#"

    def __init__(
        self,
        task_name: str,
        total: float = 100.0,
        bar_len: int = 32,
        logger=None,
    ):
        super().__init__(task_name, logger)
        self.task_name = task_name
        self.total = total
        self.bar_len = bar_len

    def __getitem__(self, key):
        if key.startswith("_"):
            return None
        return getattr(self, key, None)

    @property
    def percent(self) -> float:
        """Calculate percentage complete.

        :return: the percentage of completed, [0.0, 1.0]
        """
        return self.completed / self.total

    def update(
        self,
        steps: Optional[float] = 1.0,
        progress: Optional[float] = None,
        total: Optional[float] = None,
    ):
        """Update progress with new values.

        :param steps: Number of incremental completed steps.
        :param progress: : Number of completed steps.
        :param total: Total number of steps, or ``None`` to not change. Defaults to None.
        """

        if progress is not None:
            self.completed = progress
        else:
            self.completed += steps

        self.total = total if total is not None else self.total

        sys.stdout.write("\r")
        elapsed = time.perf_counter() - self.start

        num_bars = int(max(1, self.percent * self.bar_len))
        num_bars = num_bars % self.bar_len
        num_bars = self.bar_len if not num_bars and self.completed else max(num_bars, 1)

        suffix = self.suffix % self
        # suffix = f'{self.completed}/{self.total}'
        line = "".join(
            [
                self.task_name,
                self.bar_prefix,
                self.fill * num_bars,
                self.empty_fill * (self.bar_len - num_bars),
                self.bar_suffix,
                suffix,
            ]
        )
        sys.stdout.write(line)

        # sys.stdout.write(
        #     '{:>10} |{:<{}}| ⏱️ {:3.1f}s'.format(
        #         colored(self.task_name, 'cyan'),
        #         colored('█' * num_bars, 'green'),
        #         self.bar_len + 9,
        #         elapsed,
        #     )
        # )
        if num_bars == self.bar_len:
            sys.stdout.write("\n")
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


class ChargingBar(ProgressBar):
    """Charging Bar"""

    bar_prefix = " "
    bar_suffix = " "
    empty_fill = "∙"
    fill = "█"


class Spinner(ProgressBar):
    """Spinner"""

    phases = ("-", "\\", "|", "/")
    hide_cursor = True

    def update(
        self,
        steps: Optional[float] = 1.0,
        progress: Optional[float] = None,
        total: Optional[float] = None,
    ):
        """Update progress with new values.

        :param steps: Number of incremental completed steps.
        :param progress: : Number of completed steps.
        :param total: Total number of steps, or ``None`` to not change. Defaults to None.
        """

        if progress is not None:
            self.completed = progress
        else:
            self.completed += steps

        self.total = total if total is not None else self.total

        i = int(self.completed) % len(self.phases)

        sys.stdout.write("\r")
        elapsed = time.perf_counter() - self.start

        line = " ".join([self.task_name, self.phases[i]])
        sys.stdout.write(line)

        if self.percent >= 1.0:
            sys.stdout.write("\n")
        sys.stdout.flush()


class PieSpinner(Spinner):
    """PieSpinner"""

    phases = ["◷", "◶", "◵", "◴"]


class MoonSpinner(Spinner):
    """MoonSpinner"""

    phases = ["◑", "◒", "◐", "◓"]

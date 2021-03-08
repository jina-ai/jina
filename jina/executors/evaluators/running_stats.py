"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """

from math import sqrt


class RunningStats:
    """Computes running mean and standard deviation"""

    def __init__(self):
        """Constructor."""
        self._n = 0
        self._m = None
        self._s = None

    def clear(self):
        """Reset the stats."""
        self._n = 0.0

    @property
    def mean(self):
        """Get the running mean."""
        return self._m if self._n else 0.0

    @property
    def variance(self):
        """Get the running variance."""
        return self._s / self._n if self._n else 0.0

    @property
    def std(self):
        """Get the standard variance."""
        return sqrt(self.variance)

    def __add__(self, x: float):
        self._n += 1
        if self._n == 1:
            self._m = x
            self._s = 0.0
        else:
            prev_m = self._m
            self._m += (x - self._m) / self._n
            self._s += (x - prev_m) * (x - self._m)
        return self

    def __str__(self):
        return f'mean={self.mean:2.4f}, std={self.std:2.4f}'

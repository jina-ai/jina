__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseExecutableDriver


class DeleteDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`delete` by default.

    :param executor: Name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
    :param method: The function name of the executor that the driver feeds to, by default is 'delete'.
    :param args:
    :param kwargs:
    """

    def __init__(self, executor: str = None, method: str = 'delete', *args, **kwargs):
        """Set constructor method."""
        super().__init__(executor, method, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.exec_fn(self.req.ids)

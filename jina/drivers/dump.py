from typing import Optional

from jina.drivers import BaseExecutableDriver


class DumpDriver(BaseExecutableDriver):
    """A Driver that calls the dump method of the Executor

    :param executor: the executor to which we attach the driver
    :param args: passed to super().__init__
    :param kwargs: passed to super().__init__
    """

    def __init__(
        self,
        executor: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(executor, 'dump', *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Call the Dump method of the Indexer to which the Driver is attached

        :param args: passed to the exec_fn
        :param kwargs: passed to the exec_fn
        """
        self.exec_fn(self.req.path, self.req.shards, *args, **kwargs)

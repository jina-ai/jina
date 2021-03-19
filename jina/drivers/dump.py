from typing import Optional

from jina.drivers import BaseExecutableDriver


class DumpControlReqDriver(BaseExecutableDriver):
    def __init__(
        self,
        executor: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(executor, 'dump', *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.exec_fn(self.req.path, self.req.shards, self.req.formats, *args, **kwargs)

from typing import Optional

from jina.drivers import BaseExecutableDriver


class ReloadDriver(BaseExecutableDriver):
    def __init__(
        self,
        executor: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(executor, 'reload', *args, **kwargs)

    def __call__(self, *args, **kwargs):
        print(f'### ReloadDriver calling reload on {self.exec_fn}')
        self.exec_fn(self.req.path, *args, **kwargs)

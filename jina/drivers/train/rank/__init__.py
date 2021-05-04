from typing import Optional

from ... import BaseExecutableDriver


class RankerTrainerDriver(BaseExecutableDriver):
    """"""

    def __init__(
        self, executor: Optional[str] = None, method: str = 'train', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

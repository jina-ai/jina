__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import BaseExecutableDriver


class DeleteDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`delete` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'delete', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """
        Call base executable driver on document ids for deletion.

        :param args: unused
        :param kwargs: unused
        """
        self.exec_fn(self.req.ids)

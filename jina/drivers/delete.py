__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseExecutableDriver


class DeleteDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`delete` by default """

    def __init__(self, executor: str = None, method: str = 'delete', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        from ..executors.indexers.vector import BaseNumpyIndexer
        if isinstance(self.exec, BaseNumpyIndexer):
            keys = np.array(self.req.ids, dtype=(np.str_, self._exec.key_length))
        else:
            keys = self.req.ids

        self.exec_fn(keys)

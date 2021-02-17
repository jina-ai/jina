__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import FastRecursiveMixin, BaseExecutableDriver

if False:
    from .. import DocumentSet


class CraftDriver(FastRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: Optional[str] = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        for doc in docs:
            _args_dict = doc.get_attrs(*self.exec.required_keys)
            ret = self.exec_fn(**_args_dict)
            if ret:
                doc.set_attrs(**ret)

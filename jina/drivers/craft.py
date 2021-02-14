__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import BaseExecutableDriver

if False:
    from .. import DocumentSet


class CraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default.

    :param executor: Name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
    :param method: the function name of the executor that the driver feeds to, by default is 'craft'.
    :param args:
    :param kwargs:
    """

    def __init__(self, executor: Optional[str] = None, method: str = 'craft', *args, **kwargs):
        """Set constructor method."""
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        for doc in docs:
            _args_dict = doc.get_attrs(*self.exec.required_keys)
            ret = self.exec_fn(**_args_dict)
            if ret:
                doc.set_attrs(**ret)

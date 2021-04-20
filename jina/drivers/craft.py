__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import FlatRecursiveMixin, BaseExecutableDriver, DocsExtractUpdateMixin


class CraftDriver(DocsExtractUpdateMixin, FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'craft', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

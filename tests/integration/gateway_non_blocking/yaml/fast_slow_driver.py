__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from jina.drivers import FlatRecursiveMixin, BaseExecutableDriver
import time

if False:
    from jina import DocumentArray


class FastSlowDriver(FlatRecursiveMixin, BaseExecutableDriver):
    def __init__(
        self, executor: Optional[str] = None, method: str = 'craft', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentArray', *args, **kwargs):
        if docs:
            assert len(docs) == 1
            if docs[0].text == 'slow':
                time.sleep(2)

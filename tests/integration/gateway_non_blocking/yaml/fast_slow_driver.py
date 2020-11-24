__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from jina.drivers import BaseExecutableDriver
import time

if False:
    from jina import DocumentSet


class FastSlowDriver(BaseExecutableDriver):
    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        if docs:
            assert len(docs) == 1
            if docs[0].text == 'slow':
                time.sleep(2)

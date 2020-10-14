import os

from jina.executors.metas import get_default_metas
from tests import JinaTestCase


class ExecutorTestCase(JinaTestCase):
    @property
    def metas(self):
        metas = get_default_metas()
        if 'JINA_TEST_GPU' in os.environ:
            metas['on_gpu'] = True
        return metas

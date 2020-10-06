__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple
from jina.proto import jina_pb2

from . import BaseExecutableDriver


class EvaluateDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`evaluate` by default
    """

    def __init__(self, executor: str = None, traversal_paths: Tuple[str] = ('r',), method: str = 'evaluate', *args,
                 **kwargs):
        super().__init__(executor, method, traversal_paths=traversal_paths, *args, **kwargs)
        self._is_apply = True
        self._use_tree_traversal = True

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        doc.evaluation = self.exec_fn(doc.matches, doc.groundtruth)

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Iterable
from jina.proto import jina_pb2

from . import BaseExecutableDriver


class RankingEvaluationDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`evaluate` by default
    """

    def __init__(self, executor: str = None,
                 traversal_paths: Tuple[str] = ('r',),
                 method: str = 'evaluate',
                 id_tag='id', *args,
                 **kwargs):
        super().__init__(executor, method, traversal_paths=traversal_paths, *args, **kwargs)
        self.id_tag = id_tag

    @property
    def id(self):
        if self.pea:
            return self.pea.name
        else:
            return self.__class__.__name__

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs) -> None:
        for doc in docs:
            evaluation = doc.evaluations.add()
            matches_ids = list(map(lambda x: x.tags[self.id_tag], doc.matches))
            groundtruth_ids = list(map(lambda x: x.tags[self.id_tag], doc.groundtruth))
            evaluation.value = self.exec_fn(matches_ids, groundtruth_ids)
            evaluation.id = f'{self.id}-{self.exec.complete_name}'

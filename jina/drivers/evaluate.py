__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Iterable
from jina.proto import jina_pb2

from . import BaseExecutableDriver


class DocGroundTruthTupleWrapper:
    """
    Helper class to expose common interface to the traversal logic of the BaseExecutable Driver.
    It is important to note that it checks the matching structure of `docs` and `groundtruths`. It is important while
    traversing to ensure that then the driver can be applied at a comparable level of granularity and adjacency.
    This does not imply that you can't compare at the end a document with 10 matches with a groundtruth with 20 matches
    """

    def __init__(self, doc: 'jina_pb2.Document', groundtruth: 'jina_pb2.Document'):
        self.doc = doc
        self.groundtruth = groundtruth

    @property
    def matches(self):
        assert len(self.doc.matches) == len(self.groundtruth.matches)
        return [DocGroundTruthTupleWrapper(doc, groundtruth) for doc, groundtruth in
                zip(self.doc.matches, self.groundtruth.matches)]

    @property
    def chunks(self):
        assert len(self.doc.chunks) == len(self.groundtruth.chunks)
        return [DocGroundTruthTupleWrapper(doc, groundtruth) for doc, groundtruth in
                zip(self.doc.matches, self.groundtruth.matches)]


class BaseEvaluationDriver(BaseExecutableDriver):
    def __init__(self, executor: str = None,
                 traversal_paths: Tuple[str] = ('r',),
                 method: str = 'evaluate',
                 *args,
                 **kwargs):
        super().__init__(executor, method, traversal_paths=traversal_paths, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        assert len(self.req.docs) == len(self.req.groundtruths)
        docs_groundtruths = [DocGroundTruthTupleWrapper(doc, groundtruth) for doc, groundtruth in
                             zip(self.req.docs, self.req.groundtruths)]
        self._traverse_apply(docs_groundtruths, *args, **kwargs)

    def _apply_all(self, docs_groundtruths: Tuple[Iterable['jina_pb2.Document'], Iterable['jina_pb2.Document']],
                   context_doc_groundtruth: Tuple['jina_pb2.Document', 'jina_pb2.Document'],
                   *args,
                   **kwargs) -> None:
        pass


class RankingEvaluationDriver(BaseEvaluationDriver):
    """Drivers inherited from this Driver will bind :meth:`evaluate` by default
    """

    def __init__(self,
                 id_tag='id',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.id_tag = id_tag

    @property
    def id(self):
        if self.pea:
            return self.pea.name
        else:
            return self.__class__.__name__

    def _apply_all(self, docs_groundtruths: Tuple[Iterable['jina_pb2.Document'], Iterable['jina_pb2.Document']], *args,
                   **kwargs) -> None:
        for doc, groundtruth in docs_groundtruths:
            evaluation = doc.evaluations.add()
            matches_ids = list(map(lambda x: x.tags[self.id_tag], doc.matches))
            groundtruth_ids = list(map(lambda x: x.tags[self.id_tag], groundtruth.matches))
            evaluation.value = self.exec_fn(matches_ids, groundtruth_ids)
            evaluation.id = f'{self.id}-{self.exec.complete_name}'

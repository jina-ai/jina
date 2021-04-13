from jina.drivers.index import BaseIndexDriver
from .. import Document

# noinspection PyUnreachableCode
if False:
    from ..types.sets import DocumentSet


def _doc_without_embedding(d):
    new_doc = Document(d, copy=True)
    new_doc.ClearField('embedding')
    return new_doc


class DBMSIndexDriver(BaseIndexDriver):
    """Forwards ids, vectors, serialized Document to a BaseDBMSIndexer"""

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        info = [
            (doc.id, doc.embedding, _doc_without_embedding(doc).SerializeToString())
            for doc in docs
        ]
        if info:
            ids, vecs, metas = zip(*info)
            self.check_key_length(ids)
            self.exec_fn(ids, vecs, metas)

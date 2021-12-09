from collections import MutableSequence
from typing import Optional, Union, List, Iterator, Iterable

from jina import DocumentArray
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.proto import jina_pb2
from jina.types.document import AllMixins, Document

__all__ = ['DocumentArrayRedis']
SIZE_KEY = '__size__'


class DocumentArrayRedis(
    AllMixins,
    MutableSequence,
):
    def __init__(
        self,
        docs=None,
        host='localhost',
        port=6379,
        db=0,
        name='doc_array',
        clear=False,
    ):
        """
        :param docs:
        :param host:
        :param port:
        :param db:
        :param name:
        :param clear: whether to clear the key beforehand
        """
        with ImportExtensions(required=True):
            import walrus

        self.name = name
        self.logger = JinaLogger(f'docs-{name}')
        self._db = walrus.Database(host=host, port=port, db=db)
        # to investigate: Hash or List
        # hash has faster access
        # but no int index access?
        self.docs = self._db.Array(name)
        # if the user wants to clear they don't care if there was data there before
        if clear:
            self.clear()
        if len(self.docs):
            self.logger.info(f'Key at {name} already has {len(self.docs)} Documents')
        if docs:
            # print(f'extending with {len(docs)}')
            self.extend(docs)

    def insert(self, index: int, doc: 'Document') -> None:
        """Insert `doc` at `index`.

        :param index: the offset index of the insertion.
        :param doc: the doc needs to be inserted.
        """
        # This however must be here as inheriting from MutableSequence requires
        self.docs[index] = doc.to_bytes()

    def __len__(self):
        # print(f'calling __len__')
        # print(self.docs.__len__())
        # print(self.docs)
        return len(self.docs)

    def extend(self, docs: Iterable['Document']) -> None:
        if not docs:
            return

        for d in docs:
            self.append(d)

    def append(self, doc: 'Document') -> None:
        """
        Append `doc` in :class:`DocumentArrayRedis`.

        :param doc: The doc needs to be appended.
        """
        # TODO check if id exists so as not to create two Docs with same id
        if isinstance(doc, Document):
            self.docs.append(doc.to_bytes())
        elif isinstance(doc, jina_pb2.DocumentProto):
            self.docs.append(Document(doc).to_bytes())
        else:
            raise ValueError(f'not supported type for doc: {type(doc)}')

    def __getitem__(
        self, key: Union[int, str, slice, List]
    ) -> Optional[Union['Document', 'DocumentArray']]:
        if isinstance(key, int):
            return Document(self.docs[key])
        elif isinstance(key, slice):
            indices = list(
                range(
                    key.start or 0,
                    min(key.stop or len(self.docs), len(self.docs)),
                    key.step or 1,
                )
            )
            return_da = DocumentArray.empty(len(indices))
            for enumerate_idx, idx in enumerate(indices):
                doc_bytes = self.docs[idx]
                doc = Document(doc_bytes)
                return_da[enumerate_idx] = doc
            return return_da
        elif isinstance(key, List):
            res = []
            for k in key:
                res.append(self[k])
            return DocumentArray(res)
        elif isinstance(key, str):
            for doc_bytes in self:
                d = Document(doc_bytes)
                if d.id == key:
                    return Document(d)
        else:
            raise IndexError(f'unsupported type {type(key)}')

    def __delitem__(self, key: Union[int, str, slice]):
        if isinstance(key, int):
            del self.docs[key]
        elif isinstance(key, (slice, List)):
            for k in list(key):
                del self[k]
        elif isinstance(key, str):
            idx_del = self._index(key)
            if idx_del is not None:
                del self[idx_del]
        else:
            raise IndexError(f'unsupported type {type(key)}')

    def _index(self, key):
        idx_del = None
        for idx, d_bytes in enumerate(self.docs):
            d = Document(d_bytes)
            if d.id == key:
                idx_del = idx
                break
        return idx_del

    def __iter__(self) -> Iterator['Document']:
        for doc in self.docs:
            yield Document(doc)

    def __setitem__(self, key: Union[int, str], value: 'Document') -> None:
        if isinstance(value, Document):
            value_doc = value
            value = value.to_bytes()
        if isinstance(key, int):
            self.docs.__setitem__(key, value)
        elif isinstance(key, str):
            idx_set = self._index(key)
            if idx_set is not None:
                value_doc.id = key
                self[idx_set] = value_doc.to_bytes()
            else:
                # TODO error msg
                print(f'Document with id {key} was not found')
        else:
            raise IndexError(f'unsupported type {type(key)}')

    def __contains__(self, item: str) -> bool:
        return self[item] is not None

    def clear(self) -> None:
        self.docs.clear()
        self.docs = self._db.Array(self.name)

    def sort(self, **kwargs):
        # TODO not trivial. would need to change to List type
        # and would be v slow because you can't sort directly on the
        # bytes. you need to deserialize and then sort
        # refer to tests of DA or DAMM when implementing
        raise NotImplementedError

    def reverse(self) -> None:
        # TODO not clear if possible
        # refer to tests of DA or DAMM when implementing
        raise NotImplementedError

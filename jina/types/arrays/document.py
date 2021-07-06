import json
import warnings
from abc import abstractmethod
from collections.abc import MutableSequence, Iterable as Itr
from contextlib import nullcontext
from typing import (
    Union,
    Iterable,
    Tuple,
    List,
    Iterator,
    TextIO,
    Optional,
    Generator,
    BinaryIO,
    TypeVar,
)

from .traversable import TraversableSequence
from ..document import Document
from ...helper import typename, cached_property, cache_invalidate
from ...proto import jina_pb2

try:
    # when protobuf using Cpp backend
    from google.protobuf.pyext._message import (
        RepeatedCompositeContainer as RepeatedContainer,
    )
except:
    # when protobuf using Python backend
    from google.protobuf.internal.containers import (
        RepeatedCompositeFieldContainer as RepeatedContainer,
    )

__all__ = ['DocumentArray', 'DocumentArrayGetAttrMixin']

DocumentArraySourceType = TypeVar(
    'DocumentArraySourceType',
    jina_pb2.DocumentArrayProto,
    List[Document],
    List[jina_pb2.DocumentProto],
)

if False:
    from ..document import Document


class DocumentArrayGetAttrMixin:
    """A mixin that provides attributes getter in bulk """

    @abstractmethod
    def __iter__(self):
        ...

    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list.
        """
        return self.get_attributes_with_docs(*fields)[0]

    def get_attributes_with_docs(
        self,
        *fields: str,
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """Return all nonempty values of the fields together with their nonempty docs

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a tuple. The first element is  a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list. The second element is the non-empty docs.
        """

        contents = []
        docs_pts = []
        bad_docs = []

        for doc in self:
            r = doc.get_attributes(*fields)
            if r is None:
                bad_docs.append(doc)
                continue
            contents.append(r)
            docs_pts.append(doc)

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        if bad_docs:
            warnings.warn(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing one of the '
                f'following fields: {fields} '
            )

        if not docs_pts:
            warnings.warn('no documents are extracted')

        return contents, DocumentArray(docs_pts)


class DocumentArray(
    TraversableSequence, MutableSequence, DocumentArrayGetAttrMixin, Itr
):
    """
    :class:`DocumentArray` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentArray's using the '+' and '+=' operators.

    It is supposed to act as a view containing a pointer to a `RepeatedContainer` of `DocumentProto` while offering `Document` Jina native types
    when getting items or iterating over it

    :param docs: the document array to construct from. One can also give `DocumentArrayProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it. It also can accept a List
    """

    def __init__(self, docs: Optional[DocumentArraySourceType] = None):
        super().__init__()
        self._pb_body = []
        if docs is not None:
            if isinstance(docs, jina_pb2.DocumentArrayProto):
                # This would happen when loading from file or memmap
                self._pb_body = docs.docs
            elif isinstance(docs, RepeatedContainer):
                # This would happen when `doc.matches` or `doc.chunks`
                self._pb_body = docs
            elif isinstance(docs, DocumentArray):
                # This would happen in the client
                self._pb_body = docs._pb_body
            elif isinstance(docs, list):
                # This would happen in the client
                for doc in docs:
                    if isinstance(doc, Document):
                        self._pb_body.append(doc.proto)
                    elif isinstance(doc, jina_pb2.DocumentProto):
                        self._pb_body.append(doc)
                    else:
                        raise ValueError(f'Unexpected element in an input list')
            else:
                from .memmap import DocumentArrayMemmap

                if isinstance(docs, (Generator, DocumentArrayMemmap)):
                    docs = list(docs)
                    for doc in docs:
                        self.append(doc)
                else:
                    raise ValueError(
                        f'DocumentArray got an unexpected input {type(docs)}'
                    )

    @cache_invalidate(attribute='_id_to_index')
    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentArray` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._pb_body.insert(index, doc.proto)

    @cache_invalidate(attribute='_id_to_index')
    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, int):
            self[key].CopyFrom(value)
        elif isinstance(key, str):
            self[self._id_to_index[key]].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    @cache_invalidate(attribute='_id_to_index')
    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._pb_body[index]
        elif isinstance(index, str):
            del self[self._id_to_index[index]]
        elif isinstance(index, slice):
            del self._pb_body[index]
        else:
            raise IndexError(
                f'do not support this index type {typename(index)}: {index}'
            )

    def __eq__(self, other):
        return (
            type(self._pb_body) is type(other._pb_body)
            and self._pb_body == other._pb_body
        )

    def __len__(self):
        return len(self._pb_body)

    def __iter__(self) -> Iterator['Document']:
        from ..document import Document

        for d in self._pb_body:
            yield Document(d, hash_content=False)

    def __contains__(self, item: str):
        return item in self._id_to_index

    def __getitem__(self, item: Union[int, str, slice]):
        from ..document import Document

        if isinstance(item, int):
            return Document(self._pb_body[item])
        elif isinstance(item, str):
            return self[self._id_to_index[item]]
        elif isinstance(item, slice):
            return DocumentArray(self._pb_body[item])
        else:
            raise IndexError(f'do not support this index type {typename(item)}: {item}')

    def __add__(self, other: Iterable['Document']):
        v = DocumentArray()
        for doc in self:
            v.append(doc)
        for doc in other:
            v.append(doc)
        return v

    def __iadd__(self, other: Iterable['Document']):
        for doc in other:
            self.append(doc)
        return self

    @cache_invalidate(attribute='_id_to_index')
    def append(self, doc: 'Document'):
        """
        Append :param:`doc` in :class:`DocumentArray`.

        :param doc: The doc needs to be appended.
        """
        self._pb_body.append(doc.proto)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        for doc in iterable:
            self.append(doc)

    @cache_invalidate(attribute='_id_to_index')
    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        while len(self._pb_body) > 0:
            self._pb_body.pop()

    def reverse(self):
        """In-place reverse the sequence."""
        size = len(self._pb_body)
        hi_idx = size - 1
        for i in range(int(size / 2)):
            tmp = jina_pb2.DocumentProto()
            tmp.CopyFrom(self._pb_body[hi_idx])
            self._pb_body[hi_idx].CopyFrom(self._pb_body[i])
            self._pb_body[i].CopyFrom(tmp)
            hi_idx -= 1

    @cached_property
    def _id_to_index(self):
        """Returns a doc_id to index in list

        .. # noqa: DAR201"""
        return {d.id: i for i, d in enumerate(self._pb_body)}

    def sort(self, key=None, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param key: key callable to sort based upon
        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        if key:

            def overriden_key(proto):
                # Function to override the `proto` and wrap it around a `Document` to enable sorting via
                # `Document-like` interface
                d = Document(proto)
                return key(d)

            # Logic here: `overriden_key` is offered to allow the user sort via pythonic `Document` syntax. However,
            # maybe there may be cases where this won't work and the user may enter `proto-like` interface. To make
            # sure (quite fragile) the `sort` will work seamlessly, it tries to apply `key` to the first element and
            # see if it works. If it works it can sort with `proto` interface, otherwise use `Document` interface one.
            # (Very often the 2 interfaces are both the same and valid, so proto will have less overhead
            overriden = False
            try:
                key(self._pb_body[0])
            except:
                overriden = True

            if not overriden:
                self._pb_body.sort(key=key, *args, **kwargs)
            else:
                self._pb_body.sort(key=overriden_key, *args, **kwargs)
        else:
            self._pb_body.sort(*args, **kwargs)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __str__(self):
        from ..document import Document

        content = f'{self.__class__.__name__} has {len(self._pb_body)} items'

        if len(self._pb_body) > 3:
            content += ' (showing first three)'

        content += ':\n'
        content += ',\n'.join(str(Document(d)) for d in self._pb_body[:3])

        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._pb_body)}.items()
        )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'

    def save(
        self, file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> None:
        """Save array elements into a JSON or a binary file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary`. JSON file is human-readable,
            but binary format gives much smaller size and faster save/load speed.
        """
        if file_format == 'json':
            self.save_json(file)
        elif file_format == 'binary':
            self.save_binary(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`]')

    @classmethod
    def load(
        cls, file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> 'DocumentArray':
        """Load array elements from a JSON or a binary file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary`. JSON file is human-readable,
            but binary format gives much smaller size and faster save/load speed.

        :return: the loaded DocumentArray object
        """
        if file_format == 'json':
            return cls.load_json(file)
        elif file_format == 'binary':
            return cls.load_binary(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`]')

    def save_binary(self, file: Union[str, BinaryIO]) -> None:
        """Save array elements into a binary file.

        Comparing to :meth:`save_json`, it is faster and the file is smaller, but not human-readable.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'wb')

        with file_ctx as fp:
            dap = jina_pb2.DocumentArrayProto()
            if self._pb_body:
                dap.docs.extend(self._pb_body)
            fp.write(dap.SerializeToString())

    def save_json(self, file: Union[str, TextIO]) -> None:
        """Save array elements into a JSON file.

        Comparing to :meth:`save_binary`, it is human-readable but slower to save/load and the file size larger.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')

        with file_ctx as fp:
            for d in self:
                json.dump(d.dict(), fp)
                fp.write('\n')

    @classmethod
    def load_json(cls, file: Union[str, TextIO]) -> 'DocumentArray':
        """Load array elements from a JSON file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file)

        with file_ctx as fp:
            from ..document import Document

            da = DocumentArray()
            for v in fp:
                da.append(Document(v))
            return da

    @classmethod
    def load_binary(cls, file: Union[str, BinaryIO]) -> 'DocumentArray':
        """Load array elements from a binary file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'rb')

        dap = jina_pb2.DocumentArrayProto()

        with file_ctx as fp:
            dap.ParseFromString(fp.read())
            da = DocumentArray(dap.docs)
            return da

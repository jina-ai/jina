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
)

from .traversable import TraversableSequence
from ...helper import typename, cached_property
from ...proto.jina_pb2 import DocumentProto, DocumentArrayProto

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

    :param doc_views: A list of :class:`Document`
    :type doc_views: Optional[Union['RepeatedContainer', Iterable['Document']]]
    """

    def __init__(
        self,
        doc_views: Optional[Union['RepeatedContainer', Iterable['Document']]] = None,
    ):
        super().__init__()
        if doc_views is not None:
            from .memmap import DocumentArrayMemmap

            if isinstance(doc_views, (Generator, DocumentArrayMemmap)):
                self._doc_views = list(doc_views)
            else:
                self._doc_views = doc_views
        else:
            self._doc_views = []

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentArray` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._doc_views.insert(index, doc.proto)

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, int):
            self[key].CopyFrom(value)
        elif isinstance(key, str):
            self[self._id_to_index[key]].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._doc_views[index]
        elif isinstance(index, str):
            del self[self._id_to_index[index]]
        elif isinstance(index, slice):
            del self._doc_views[index]
        else:
            raise IndexError(
                f'do not support this index type {typename(index)}: {index}'
            )

    def __eq__(self, other):
        return (
            type(self._doc_views) is type(other._doc_views)
            and self._doc_views == other._doc_views
        )

    def __len__(self):
        return len(self._doc_views)

    def __iter__(self) -> Iterator['Document']:
        from ..document import Document

        for d in self._doc_views:
            if not isinstance(d, Document):
                yield Document(d)
            else:
                yield d

    def __contains__(self, item: str):
        return item in self._id_to_index

    def __getitem__(self, item: Union[int, str, slice]):
        from ..document import Document

        if isinstance(item, int):
            view = self._doc_views[item]
            if not isinstance(view, Document):
                return Document(view)
            else:
                return view
        elif isinstance(item, str):
            return self[self._id_to_index[item]]
        elif isinstance(item, slice):
            return DocumentArray(self._doc_views[item])
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

    def append(self, doc: 'Document'):
        """
        Append :param:`doc` in :class:`DocumentArray`.

        :param doc: The doc needs to be appended.
        """
        self._doc_views.append(doc.proto)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        del self._doc_views[:]

    def reverse(self):
        """In-place reverse the sequence."""
        if isinstance(self._doc_views, RepeatedContainer):
            size = len(self._doc_views)
            hi_idx = size - 1
            for i in range(int(size / 2)):
                tmp = DocumentProto()
                tmp.CopyFrom(self._doc_views[hi_idx])
                self._doc_views[hi_idx].CopyFrom(self._doc_views[i])
                self._doc_views[i].CopyFrom(tmp)
                hi_idx -= 1
        elif isinstance(self._doc_views, list):
            self._doc_views.reverse()

    @cached_property
    def _id_to_index(self):
        """Returns a doc_id to index in list

        .. # noqa: DAR201"""
        return {d.id: i for i, d in enumerate(self._doc_views)}

    def sort(self, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        self._doc_views.sort(*args, **kwargs)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __str__(self):
        from ..document import Document

        if hasattr(self._doc_views, '__len__'):
            content = f'{self.__class__.__name__} has {len(self._doc_views)} items'

            if len(self._doc_views) > 3:
                content += ' (showing first three)'
        else:
            content = 'unknown length array'

        content += ':\n'
        content += ',\n'.join(str(Document(d)) for d in self._doc_views[:3])

        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._doc_views)}.items()
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
            dap = DocumentArrayProto()
            if self._doc_views:
                if isinstance(self._doc_views[0], DocumentProto):
                    dap.docs.extend(self._doc_views)
                else:
                    dap.docs.extend([d.proto for d in self._doc_views])
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

        dap = DocumentArrayProto()

        with file_ctx as fp:
            dap.ParseFromString(fp.read())
            da = DocumentArray(dap.docs)
            return da

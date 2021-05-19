import csv
import glob
import itertools
import json
import os
import random
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
    Dict,
)

import numpy as np


from .traversable import TraversableSequence
from ...helper import typename, cached_property
from ...logging import default_logger
from ...proto.jina_pb2 import DocumentProto

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

__all__ = ['DocumentArray']

if False:
    from ..document import Document

# https://github.com/ndjson/ndjson.github.io/issues/1#issuecomment-109935996
_jsonl_ext = {'.jsonlines', '.ndjson', '.jsonl', '.jl', '.ldjson'}
_csv_ext = {'.csv', '.tcsv'}


def _sample(iterable, sampling_rate: Optional[float] = None):
    for i in iterable:
        if sampling_rate is None or random.random() < sampling_rate:
            yield i


def _subsample(
    iterable, size: Optional[int] = None, sampling_rate: Optional[float] = None
):
    yield from itertools.islice(_sample(iterable, sampling_rate), size)


class DocumentArray(TraversableSequence, MutableSequence, Itr):
    """
    :class:`DocumentArray` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentArray's using the '+' and '+=' operators.

    :param docs_proto: A list of :class:`Document`
    :type docs_proto: Optional[Union['RepeatedContainer', Iterable['Document']]]
    """

    def __init__(
        self,
        docs_proto: Optional[Union['RepeatedContainer', Iterable['Document']]] = None,
    ):
        super().__init__()
        if docs_proto is not None:
            if isinstance(docs_proto, Generator):
                self._docs_proto = list(docs_proto)
            else:
                self._docs_proto = docs_proto
        else:
            self._docs_proto = []

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentArray` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._docs_proto.insert(index, doc.proto)

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, (int, str)):
            self[key].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._docs_proto[index]
        elif isinstance(index, str):
            del self._docs_map[index]
        elif isinstance(index, slice):
            del self._docs_proto[index]
        else:
            raise IndexError(
                f'do not support this index type {typename(index)}: {index}'
            )

    def __eq__(self, other):
        return (
            type(self._docs_proto) is type(other._docs_proto)
            and self._docs_proto == other._docs_proto
        )

    def __len__(self):
        return len(self._docs_proto)

    def __iter__(self) -> Iterator['Document']:
        from ..document import Document

        for d in self._docs_proto:
            yield Document(d)

    def __contains__(self, item: str):
        return item in self._docs_map

    def __getitem__(self, item: Union[int, str, slice]):
        from ..document import Document

        if isinstance(item, int):
            return Document(self._docs_proto[item])
        elif isinstance(item, str):
            return Document(self._docs_map[item])
        elif isinstance(item, slice):
            return DocumentArray(self._docs_proto[item])
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
        self._docs_proto.append(doc.proto)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        del self._docs_proto[:]

    def reverse(self):
        """In-place reverse the sequence."""
        if isinstance(self._docs_proto, RepeatedContainer):
            size = len(self._docs_proto)
            hi_idx = size - 1
            for i in range(int(size / 2)):
                tmp = DocumentProto()
                tmp.CopyFrom(self._docs_proto[hi_idx])
                self._docs_proto[hi_idx].CopyFrom(self._docs_proto[i])
                self._docs_proto[i].CopyFrom(tmp)
                hi_idx -= 1
        elif isinstance(self._docs_proto, list):
            self._docs_proto.reverse()

    @cached_property
    def _docs_map(self):
        """Returns a doc_id to doc mapping so one can later index a Document using doc_id as string key.

        .. # noqa: DAR201"""
        return {d.id: d for d in self._docs_proto}

    def sort(self, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        self._docs_proto.sort(*args, **kwargs)

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
            default_logger.warning(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing one of the '
                f'following fields: {fields} '
            )

        if not docs_pts:
            default_logger.warning('no documents are extracted')

        return contents, DocumentArray(docs_pts)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __str__(self):
        from ..document import Document

        if hasattr(self._docs_proto, '__len__'):
            content = f'{self.__class__.__name__} has {len(self._docs_proto)} items'

            if len(self._docs_proto) > 3:
                content += ' (showing first three)'
        else:
            content = 'unknown length array'

        content += ':\n'
        content += ',\n'.join(str(Document(d)) for d in self._docs_proto[:3])

        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._docs_proto)}.items()
        )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'

    def save(self, file: Union[str, TextIO]) -> None:
        """Save array elements into a JSON file.

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

    @staticmethod
    def load(file: Union[str, TextIO]) -> 'DocumentArray':
        """Load array elements from a JSON file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file)

        from jina import Document

        da = DocumentArray()
        with file_ctx as fp:
            for v in fp:
                da.append(Document(v))
        return da

    @staticmethod
    def from_lines(
        lines: Optional[Iterable[str]] = None,
        filepath: Optional[str] = None,
        read_mode: str = 'r',
        line_format: str = 'json',
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
    ) -> Generator['Document', None, None]:
        """Generator function for lines, json and csv. Yields documents or strings.

        :param lines: a list of strings, each is considered as a document
        :param filepath: a text file that each line contains a document
        :param read_mode: specifies the mode in which the file
                    is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param line_format: the format of each line ``json`` or ``csv``
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :yield: documents

        """
        if filepath:
            file_type = os.path.splitext(filepath)[1]
            with open(filepath, read_mode) as f:
                if file_type in _jsonl_ext:
                    yield from DocumentArray.from_ndjson(f)
                elif file_type in _csv_ext:
                    yield from DocumentArray.from_csv(
                        f, field_resolver, size, sampling_rate
                    )
                else:
                    yield from _subsample(f, size, sampling_rate)
        elif lines:
            if line_format == 'json':
                yield from DocumentArray.from_ndjson(lines)
            elif line_format == 'csv':
                yield from DocumentArray.from_csv(
                    lines, field_resolver, size, sampling_rate
                )
            else:
                yield from _subsample(lines, size, sampling_rate)
        else:
            raise ValueError('"filepath" and "lines" can not be both empty')

    @staticmethod
    def from_ndjson(
        fp: Iterable[str],
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
    ) -> Generator['Document', None, None]:
        """Generator function for line separated JSON. Yields documents.

        :param fp: file paths
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :yield: documents

        """
        from jina import Document

        for line in _subsample(fp, size, sampling_rate):
            value = json.loads(line)
            if 'groundtruth' in value and 'document' in value:
                yield Document(value['document'], field_resolver), Document(
                    value['groundtruth'], field_resolver
                )
            else:
                yield Document(value, field_resolver)

    @staticmethod
    def from_csv(
        fp: Iterable[str],
        field_resolver: Optional[Dict[str, str]] = None,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
    ) -> Generator['Document', None, None]:
        """Generator function for CSV. Yields documents.

        :param fp: file paths
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :yield: documents

        """
        from jina import Document

        lines = csv.DictReader(fp)
        for value in _subsample(lines, size, sampling_rate):
            if 'groundtruth' in value and 'document' in value:
                yield Document(value['document'], field_resolver), Document(
                    value['groundtruth'], field_resolver
                )
            else:
                yield Document(value, field_resolver)

    @staticmethod
    def from_files(
        patterns: Union[str, List[str]],
        recursive: bool = True,
        size: Optional[int] = None,
        sampling_rate: Optional[float] = None,
        read_mode: Optional[str] = None,
    ) -> Generator['Document', None, None]:
        """Creates an iterator over a list of file path or the content of the files.

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files
            and zero or more directories and subdirectories
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file is opened.
            'r' for reading in text mode, 'rb' for reading in binary mode.
            If `read_mode` is None, will iterate over filenames.
        :yield: file paths or binary content

        .. note::
            This function should not be directly used, use :meth:`Flow.index_files`, :meth:`Flow.search_files` instead
        """
        from jina import Document

        if read_mode not in {'r', 'rb', None}:
            raise RuntimeError(
                f'read_mode should be "r", "rb" or None, got {read_mode}'
            )

        def _iter_file_exts(ps):
            return itertools.chain.from_iterable(
                glob.iglob(p, recursive=recursive) for p in ps
            )

        d = 0
        if isinstance(patterns, str):
            patterns = [patterns]
        for g in _iter_file_exts(patterns):
            if sampling_rate is None or random.random() < sampling_rate:
                if read_mode is None:
                    yield Document(uri=g)
                elif read_mode in {'r', 'rb'}:
                    with open(g, read_mode) as fp:
                        yield Document(content=fp.read())
                d += 1
            if size is not None and d > size:
                break

    @staticmethod
    def from_ndarray(
        array: 'np.ndarray',
        axis: int = 0,
        size: Optional[int] = None,
        shuffle: bool = False,
    ) -> Generator['Document', None, None]:
        """Create a generator for a given dimension of a numpy array.

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the numpy data source beforehand
        :yield: ndarray

        .. note::
            This function should not be directly used, use :meth:`Flow.index_ndarray`, :meth:`Flow.search_ndarray` instead
        """

        from jina import Document

        if shuffle:
            # shuffle for random query
            array = np.take(array, np.random.permutation(array.shape[0]), axis=axis)
        d = 0
        for r in array:
            yield Document(content=r)
            d += 1
            if size is not None and d >= size:
                break

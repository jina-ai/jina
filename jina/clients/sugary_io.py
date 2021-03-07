"""A module for sugary API wrapper around the clients."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import csv
import glob
import itertools as it
import json
import os
import random
from typing import List, Union, Iterator, Iterable, Dict, Generator, Optional

import numpy as np

if False:
    from jina import Document

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
    yield from it.islice(_sample(iterable, sampling_rate), size)


def _input_lines(
    lines: Optional[Iterable[str]] = None,
    filepath: Optional[str] = None,
    read_mode: str = 'r',
    line_format: str = 'json',
    field_resolver: Optional[Dict[str, str]] = None,
    size: Optional[int] = None,
    sampling_rate: Optional[float] = None,
) -> Generator[Union[str, 'Document'], None, None]:
    """Generator function for lines, json and sc. Yields documents or strings.

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
    :yields: documents

    .. note::
    This function should not be directly used, use :meth:`Flow.index_files`, :meth:`Flow.search_files` instead
    """
    if filepath:
        file_type = os.path.splitext(filepath)[1]
        with open(filepath, read_mode) as f:
            if file_type in _jsonl_ext:
                yield from _input_ndjson(f)
            elif file_type in _csv_ext:
                yield from _input_csv(f, field_resolver, size, sampling_rate)
            else:
                yield from _subsample(f, size, sampling_rate)
    elif lines:
        if line_format == 'json':
            yield from _input_ndjson(lines)
        elif line_format == 'csv':
            yield from _input_csv(lines, field_resolver, size, sampling_rate)
        else:
            yield from _subsample(lines, size, sampling_rate)
    else:
        raise ValueError('"filepath" and "lines" can not be both empty')


def _input_ndjson(
    fp: Iterable[str],
    field_resolver: Optional[Dict[str, str]] = None,
    size: Optional[int] = None,
    sampling_rate: Optional[float] = None,
):
    from jina import Document

    for line in _subsample(fp, size, sampling_rate):
        value = json.loads(line)
        if 'groundtruth' in value and 'document' in value:
            yield Document(value['document'], field_resolver), Document(
                value['groundtruth'], field_resolver
            )
        else:
            yield Document(value, field_resolver)


def _input_csv(
    fp: Iterable[str],
    field_resolver: Optional[Dict[str, str]] = None,
    size: Optional[int] = None,
    sampling_rate: Optional[float] = None,
):
    from jina import Document

    lines = csv.DictReader(fp)
    for value in _subsample(lines, size, sampling_rate):
        if 'groundtruth' in value and 'document' in value:
            yield Document(value['document'], field_resolver), Document(
                value['groundtruth'], field_resolver
            )
        else:
            yield Document(value, field_resolver)


def _input_files(
    patterns: Union[str, List[str]],
    recursive: bool = True,
    size: Optional[int] = None,
    sampling_rate: Optional[float] = None,
    read_mode: Optional[str] = None,
) -> Iterator[Union[str, bytes]]:
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
    if read_mode not in {'r', 'rb', None}:
        raise RuntimeError(f'read_mode should be "r", "rb" or None, got {read_mode}')

    def _iter_file_exts(ps):
        return it.chain.from_iterable(glob.iglob(p, recursive=recursive) for p in ps)

    d = 0
    if isinstance(patterns, str):
        patterns = [patterns]
    for g in _iter_file_exts(patterns):
        if sampling_rate is None or random.random() < sampling_rate:
            if read_mode is None:
                yield g
            elif read_mode in {'r', 'rb'}:
                with open(g, read_mode) as fp:
                    yield fp.read()
            d += 1
        if size is not None and d > size:
            break


def _input_ndarray(
    array: 'np.ndarray',
    axis: int = 0,
    size: Optional[int] = None,
    shuffle: bool = False,
) -> Generator['np.ndarray', None, None]:
    """Create a generator for a given dimension of a numpy array.

    :param array: the numpy ndarray data source
    :param axis: iterate over that axis
    :param size: the maximum number of the sub arrays
    :param shuffle: shuffle the numpy data source beforehand
    :yield: ndarray

    .. note::
        This function should not be directly used, use :meth:`Flow.index_ndarray`, :meth:`Flow.search_ndarray` instead
    """
    if shuffle:
        # shuffle for random query
        array = np.take(array, np.random.permutation(array.shape[0]), axis=axis)
    d = 0
    for r in array:
        yield r
        d += 1
        if size is not None and d >= size:
            break


# for back-compatibility
_input_numpy = _input_ndarray

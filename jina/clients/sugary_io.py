"""A module for sugary API wrapper around the clients."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import csv
import glob
import itertools as it
import json
import os
import random
from typing import List, Union, Iterator, Any, Iterable, Dict

import numpy as np

# https://github.com/ndjson/ndjson.github.io/issues/1#issuecomment-109935996
_jsonl_ext = {'.jsonlines', '.ndjson', '.jsonl', '.jl', '.ldjson'}
_csv_ext = {'.csv', '.tcsv'}


def _sample(iterable, sampling_rate: float = None):
    for i in iterable:
        if sampling_rate is None or random.random() < sampling_rate:
            yield i


def _subsample(iterable, sampling_rate: float = None, size: int = None, **kwargs):
    yield from it.islice(_sample(iterable, sampling_rate), size)


def _input_lines(
        lines: Iterable[str] = None,
        filepath: str = None,
        read_mode: str = 'r',
        line_format: str = 'json',
        **kwargs
) -> Iterator[Union[str, bytes]]:
    """Input function that iterates over list of strings, it can be used in the Flow API.

    :param filepath: a text file that each line contains a document
    :param lines: a list of strings, each is considered as a document
    :param size: the maximum number of the documents
    :param sampling_rate: the sampling rate between [0, 1]
    :param read_mode: specifies the mode in which the file
            is opened. 'r' for reading in text mode, 'rb' for reading in binary
    :param line_format: the format of each line ``json`` or ``csv``

    .. note::
        This function should not be directly used, use :meth:`Flow.index_lines`, :meth:`Flow.search_lines` instead
    """
    if filepath:
        file_type = os.path.splitext(filepath)[1]
        with open(filepath, read_mode) as f:
            if file_type in _jsonl_ext:
                yield from _input_ndjson(f, **kwargs)
            elif file_type in _csv_ext:
                yield from _input_csv(f, **kwargs)
            else:
                yield from _subsample(f, **kwargs)
    elif lines:
        if line_format == 'json':
            yield from _input_ndjson(lines, **kwargs)
        elif line_format == 'csv':
            yield from _input_csv(lines, **kwargs)
        else:
            yield from _subsample(lines, **kwargs)
    else:
        raise ValueError('"filepath" and "lines" can not be both empty')

def _input_ndjson(
        fp: Iterable[str],
        field_resolver: Dict[str, str] = None,
        **kwargs
):
    from jina import Document

    for line in _subsample(fp, **kwargs):
        value = json.loads(line)
        if 'groundtruth' in value and 'document' in value:
            yield Document(value['document'], field_resolver), Document(value['groundtruth'], field_resolver)
        else:
            yield Document(value, field_resolver)


def _input_csv(
        fp: Iterable[str],
        field_resolver: Dict[str, str] = None,
        **kwargs
):
    from jina import Document
    lines = csv.DictReader(fp)
    for value in _subsample(lines, **kwargs):
        if 'groundtruth' in value and 'document' in value:
            yield Document(value['document'], field_resolver), Document(value['groundtruth'], field_resolver)
        else:
            yield Document(value, field_resolver)


def _input_files(
        patterns: Union[str, List[str]],
        recursive: bool = True,
        size: int = None,
        sampling_rate: float = None,
        read_mode: str = None,
) -> Iterator[Union[str, bytes]]:
    r"""Input function that iterates over files, it can be used in the Flow API.

    :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
    :param recursive: If recursive is true, the pattern '**' will match any files and
                zero or more directories and subdirectories
    :param size: the maximum number of the files
    :param sampling_rate: the sampling rate between [0, 1]
    :param read_mode: specifies the mode in which the file
            is opened. 'r' for reading in text mode, 'rb' for reading in binary mode.
            If `read_mode` is None, will iterate over filenames

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
        array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False
) -> Iterator[Any]:
    """Input function that iterates over a numpy array, it can be used in the Flow API.

    :param array: the numpy ndarray data source
    :param axis: iterate over that axis
    :param size: the maximum number of the sub arrays
    :param shuffle: shuffle the numpy data source beforehand

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

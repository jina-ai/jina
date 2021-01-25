__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import glob
import itertools as it
import json
import random
from typing import List, Union, Iterator, Any

import numpy as np


def _input_lines(
        lines: Iterator[str] = None,
        filepath: str = None,
        size: int = None,
        sampling_rate: float = None,
        read_mode='r',
) -> Iterator[Union[str, bytes]]:
    """Input function that iterates over list of strings, it can be used in the Flow API

    :param filepath: a text file that each line contains a document
    :param lines: a list of strings, each is considered as a document
    :param size: the maximum number of the documents
    :param sampling_rate: the sampling rate between [0, 1]
    :param read_mode: specifies the mode in which the file
            is opened. 'r' for reading in text mode, 'rb' for reading in binary

    .. note::
        This function should not be directly used, use :meth:`Flow.index_lines`, :meth:`Flow.search_lines` instead
    """

    def sample(iterable):
        for i in iterable:
            if sampling_rate is None or random.random() < sampling_rate:
                yield i

    if filepath:
        file_type = filepath.split('.')[-1]
        with open(filepath, read_mode) as f:
            for line in it.islice(sample(f), size):
                if file_type == 'jsonlines':
                    value = json.loads(line)
                    if 'groundtruth' in value:
                        yield (value['document'], value['groundtruth'])
                    else:
                        yield value
                else:
                    yield line
    elif lines:
        for line in it.islice(sample(lines), size):
            yield line
    else:
        raise ValueError('"filepath" and "lines" can not be both empty')


def _input_files(
        patterns: Union[str, List[str]],
        recursive: bool = True,
        size: int = None,
        sampling_rate: float = None,
        read_mode: str = None,
) -> Iterator[Union[str, bytes]]:
    """Input function that iterates over files, it can be used in the Flow API

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

    def iter_file_exts(ps):
        return it.chain.from_iterable(glob.iglob(p, recursive=recursive) for p in ps)

    d = 0
    if isinstance(patterns, str):
        patterns = [patterns]
    for g in iter_file_exts(patterns):
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
    """Input function that iterates over a numpy array, it can be used in the Flow API

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

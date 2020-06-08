__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import glob
import itertools as it
import random
from typing import List, Union, Iterator

import numpy as np


def input_lines(lines: Iterator[str] = None, filepath: str = None, size: int = None, sampling_rate: float = None,
                read_mode='r'):
    """ Input function that iterates over list of strings, it can be used in the Flow API

    :param filepath: a text file that each line contains a document
    :param lines: a list of strings, each is considered as a document
    :param size: the maximum number of the documents
    :param sampling_rate: the sampling rate between [0, 1]
    :param read_mode: specifies the mode in which the file
            is opened. 'r' for reading in text mode, 'rb' for reading in binary
    """
    if filepath:
        fp = open(filepath, read_mode)
    elif lines:
        fp = lines
    else:
        raise ValueError('"filepath" and "lines" can not be both empty')

    d = 0
    for l in fp:
        if sampling_rate is None or random.random() < sampling_rate:
            yield l
            d += 1
        if size is not None and d > size:
            break

    if filepath:
        fp.close()


def input_files(patterns: Union[str, List[str]], recursive: bool = True,
                size: int = None, sampling_rate: float = None, read_mode: str = None):
    """ Input function that iterates over files, it can be used in the Flow API

    :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
    :param recursive: If recursive is true, the pattern '**' will match any files and
                zero or more directories and subdirectories.
    :param size: the maximum number of the files
    :param sampling_rate: the sampling rate between [0, 1]
    :param read_mode: specifies the mode in which the file
            is opened. 'r' for reading in text mode, 'rb' for reading in binary
    """

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


def input_numpy(array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False):
    """ Input function that iterates over a numpy array, it can be used in the Flow API

    :param array: the numpy ndarray data source
    :param axis: iterate over that axis
    :param size: the maximum number of the sub arrays
    :param shuffle: shuffle the numpy data source beforehand
    """
    if shuffle:
        # shuffle for random query
        array = np.take(array, np.random.permutation(array.shape[0]), axis=axis)
    d = 0
    for r in array:
        yield r
        d += 1
        if size is not None and d > size:
            break

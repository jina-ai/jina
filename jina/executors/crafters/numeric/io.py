__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np
from jina.executors.crafters import BaseDocCrafter


class ArrayStringReader(BaseDocCrafter):
    """
    :class:`ArrayStringReader` convertsthe string of numbers into a numpy array and save to the Document.
        Numbers are split on the provided delimiter, default is comma (,)
    """

    def __init__(self, delimiter: str = ',', as_type: str = 'float32', *args, **kwargs):
        """
        :param delimiter: delimiter between numbers
        :param as_type: type of number
        """
        super().__init__(*args, **kwargs)
        self.delimiter = delimiter
        self.as_type = as_type

    def craft(self, text: str, doc_id: int, *args, **kwargs) -> Dict:
        """
        Split string into numbers and convert to numpy array

        :param text: the raw text
        :param doc_id: the doc id
        :return: a dod dict with the numpy array
        """
        _string = text.split(self.delimiter)
        _array = np.array(_string)

        try:
            _array = _array.astype(self.as_type)
        except TypeError:
            self.logger.error(
                f'Data type {self.as_type} is not understood. '
                f'Please refer to the list of data types from Numpy.')
        except ValueError:
            self.logger.error(
                f'Data type mismatch. Cannot convert input to {self.as_type}.')

        return dict(doc_id=doc_id, weight=1., blob=_array)


class ArrayBytesReader(BaseDocCrafter):
    """
    :class:`ArrayBytesReader` converts a byte stream into a numpy array and save to the Document.
        The size of the vectors is provided in the constructor so that the numpy array can be interpreted properly
    """

    def __init__(self, as_type: str = 'float32', *args, **kwargs):
        """
        :param as_type: type of number
        """
        super().__init__(*args, **kwargs)
        self.as_type = as_type

    def craft(self, buffer: bytes, doc_id: int, *args, **kwargs) -> Dict:
        """
        Split string into numbers and convert to numpy array

        :param buffer: the bytes representing the array
        :param doc_id: the doc id
        :return: a chunk dict with the numpy array
        """
        _array = np.frombuffer(buffer, self.as_type)
        return dict(doc_id=doc_id, weight=1., blob=_array)

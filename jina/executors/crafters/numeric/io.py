__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List

import numpy as np
from jina.executors.crafters import BaseDocCrafter


class ArrayReader(BaseDocCrafter):
    """
    :class:`ArrayReader` convert the string of numbers into a numpy array and save to the Chunk.
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
        :return: a chunk dict with the numpy array
        """
        _string = text.split(self.delimiter)
        _array = np.array(_string)

        try:
            _array = _array.astype(self.as_type)
        except TypeError:
            self.logger.error(
                f'Data type {self.as_type} is not understood. '
                f'Please refer to the list of data types from Numpy.')
        except ValueError as e:
            self.logger.error(
                f'Data type mismatch. Cannot convert input to {self.as_type}.')

        return dict(doc_id=doc_id, offset=0, weight=1., blob=_array)

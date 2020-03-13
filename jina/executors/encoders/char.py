import numpy as np

from . import BaseTextEncoder


class OneHotTextEncoder(BaseTextEncoder):
    """

    One-hot Encoder encodes the characters into one-hot vectors. ONLY FOR TESTING USAGES.
    """
    def __init__(self,
                 on_value: float = 1,
                 off_value: float = 0,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 32
        self.dim = 127 - 32 + 1
        self.on_value = on_value
        self.off_value = off_value

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: each row is one character, an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        output = []
        for r in data:
            indices_list = [ord(c) - self.offset for c in r if self.offset <= ord(c) <= 127]
            output.append(self._onehot(indices_list, self.dim))
        return np.array(output)

    @staticmethod
    def _onehot(indices, depth, on_value=1, off_value=0):
        output = [off_value] * depth
        for idx in indices:
            if idx >= depth:
                raise ValueError("invalid index: {}".format(idx))
            output[idx] = on_value
        return output


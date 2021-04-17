__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

import numpy as np

from .. import BaseNumericEncoder
from ...decorators import batching
from ....excepts import UndefinedModel


class TransformEncoder(BaseNumericEncoder):
    """
    :class:`TransformEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`

    :param model_path: path from where to pickle the sklearn model.
    :param args: Extra positional arguments to be set
    :param kwargs: Extra keyword arguments to be set
    """

    def __init__(self, model_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_path = model_path

    def post_init(self) -> None:
        """Load the model from path if :param:`model_path` is set."""
        import pickle

        self.model = None
        if self.model_path:
            with open(self.model_path, 'rb') as model_file:
                self.model = pickle.load(model_file)

    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        :param args: Extra positional arguments to be set
        :param kwargs: Extra keyword arguments to be set
        """
        return self.model.transform(data)

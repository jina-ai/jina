__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


import numpy as np
from typing import Dict, Any
from jina.executors.decorators import batching, as_ndarray
from .. import BaseEncoder


class BaseMultiModalEncoder(BaseEncoder):
    """
    :class:`TransformEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`
    """

    def __init__(self,
                 *args,
                 **kwargs):
        """
        :param model_path: path from where to pickle the sklearn model.
        """
        super().__init__(*args, **kwargs)

    # TODO: Think if `batching` can be used in this case
    @batching
    @as_ndarray
    def encode(self, data: Dict[str, Any], *args, **kwargs) -> 'np.ndarray':
        raise NotImplementedError

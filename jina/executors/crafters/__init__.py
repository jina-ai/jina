__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from typing import Dict, List

from .. import BaseExecutor
from ...helper import typename


class BaseCrafter(BaseExecutor):
    """A :class:`BaseCrafter` transforms the content of `DocumentProto` or `Chunk`. It can be used for preprocessing,
    segmenting etc. It is an interface for Crafters which is a family of executors intended to apply
    transformations to single documents.
    The apply function is :func:`craft`, where the name of the arguments will be used as keys of the content.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {k for k in inspect.getfullargspec(self.craft).args if k != 'self'}
        if not self.required_keys:
            self.logger.warning(f'{typename(self)} works on keys, but no keys are specified')

    def craft(self, *args, **kwargs) -> Dict:
        """The apply function of this executor.
        The name of the arguments are used as keys, which are then used to tell :class:`Driver` what information to extract
        from the protobuf request accordingly. Therefore the name of the arguments should be always valid keys defined
        in the protobuf.
        """
        raise NotImplementedError


class BaseSegmenter(BaseCrafter):
    """:class:`BaseSegmenter` works on doc-level,
        it receives value on the doc-level and returns new value on the chunk-level """

    def craft(self, *args, **kwargs) -> List[Dict]:
        """The apply function of this executor.
        Unlike :class:`BaseCrafter`, the :func:`craft` here works on doc-level info and the output is defined on
        chunk-level. Therefore the name of the arguments should be always valid keys defined
        in the doc-level protobuf whereas the output dict keys should always be valid keys defined in the chunk-level
        protobuf.
        :return: a list of chunks-level info represented by a dict
        """
        raise NotImplementedError

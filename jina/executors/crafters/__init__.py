__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from typing import Dict, List

from .. import BaseExecutor


class BaseCrafter(BaseExecutor):
    """A :class:`BaseCrafter` craft the content of `Document` or `Chunk`. It can be used for preprocessing,
    segmenting etc.

    The apply function is :func:`craft`, where the name of the arguments will be used as keys of the content.

    .. seealso::
        :mod:`jina.drivers.handlers.craft`
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {k for k in inspect.getfullargspec(self.craft).args if k != 'self'}
        if not self.required_keys:
            self.logger.warning(f'{self.__class__} works on keys, but no keys are specified')

    def craft(self, *args, **kwargs) -> Dict:
        """The apply function of this executor.

        The name of the arguments are used as keys, which are then used to tell :class:`Driver` what information to extract
        from the protobuf request accordingly. Therefore the name of the arguments should be always valid keys defined
        in the protobuf.
        """
        raise NotImplementedError


class BaseChunkCrafter(BaseCrafter):
    """:class:`BaseChunkCrafter` works on chunk-level and returns new value on chunk-level.

    The example below shows a dummy transformer add ``doc_id`` to the ``chunk_id`` and use it as the new ``chunk_id``.

    .. highlight:: python
    .. code-block:: python

        class DummyTransformer(BaseDocCrafter):
            def craft(chunk_id, doc_id):
                return {'chunk_id': doc_id + chunk_id}

    """
    pass


class BaseDocCrafter(BaseCrafter):
    """:class:`BaseDocCrafter` works on doc-level and returns new value on doc-level.

    The example below shows a dummy transformer add one to the ``doc_id`` and use it as the new ``doc_id``.

    .. highlight:: python
    .. code-block:: python

        class DummyTransformer(BaseDocCrafter):
            def craft(chunk_id, doc_id):
                return {'doc_id': doc_id + 1}

    """
    pass


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

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .running_stats import RunningStats
from .. import BaseExecutor
from ..compound import CompoundExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` is used to evaluate different messages coming from any kind of executor"""

    metric = ''  #: Get the name of the evaluation metric

    def post_init(self):
        """Initialize running stats."""
        super().post_init()
        self._running_stats = RunningStats()

    def evaluate(self, actual: Any, desired: Any, *args, **kwargs) -> float:
        """Evaluates difference between param:`actual` and `param:desired`, needs to be implemented in subclass."""
        raise NotImplementedError

    @property
    def mean(self) -> float:
        """Get the running mean."""
        return self._running_stats.mean

    @property
    def std(self) -> float:
        """Get the running standard variance."""
        return self._running_stats.std

    @property
    def variance(self) -> float:
        """Get the running variance."""
        return self._running_stats.variance


class FileBasedEvaluator(CompoundExecutor):

    """A Frequently used pattern for combining A :class:`BinaryPbIndexer` and :class:`BaseEvaluator`.
     It will be equipped with predefined ``requests.on`` behaviors:

         -  At evaluation time(query or index)
             - 1. Checks for the incoming document, gets its value from the `BinaryPbIndexer` and fills the `groundtruth of the request
             - 2. Filter the documents that do not have a corresponding groundtruth
             - 3. The BaseEvaluator works as if the `groundtruth` had been provided by the client as it comes in the request.

    .. warning::
        The documents that are not found to have an indexed groundtruth are removed from the `request` so that the `Evaluator` only
        works with documents which have groundtruth.

     One can use the :class:`FileBasedEvaluator` via

     .. highlight:: yaml
     .. code-block:: yaml

         !FileBasedEvaluator
         components:
           - !BinaryPbIndexer
             with:
               index_filename: ground_truth.gz
             metas:
               name: groundtruth_index  # a customized name
               workspace: ${{TEST_WORKDIR}}
           - !BaseEvaluator

     Without defining any ``requests.on`` logic. When load from this YAML, it will be auto equipped with

     .. highlight:: yaml
     .. code-block:: yaml

         on:
           [SearchRequest, IndexRequest]:
             - !LoadGroundTruthDriver
               with:
                 executor: BaseKVIndexer
             - !BaseEvaluateDriver
               with:
                 executor: BaseEvaluator
           ControlRequest:
             - !ControlReqDriver {}
    """

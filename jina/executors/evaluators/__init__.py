__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseExecutor
from ..compound import CompoundExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` is used to evaluate different messages coming from any kind of executor
    """

    def post_init(self):
        super().post_init()
        self.num_documents = 0
        self.sum = 0

    @property
    def avg(self):
        if self.num_documents == 0:
            return 0.0
        return self.sum / self.num_documents

    @property
    def metric(self):
        """Get the name of the evaluation metric """
        pass

    def evaluate(self, prediction: Any, groundtruth: Any, *args, **kwargs) -> float:
        raise NotImplementedError


class FileBasedEvaluator(CompoundExecutor):
    """A Frequently used pattern for combining A :class:`BaseKVIndexer` and :class:`BaseEvaluator`.
     It will be equipped with predefined ``requests.on`` behaviors:

         -  At evaluation time(query or index)
             - 1. Checks for the incoming document, gets its value from the `BaseKVIndexer` and fills the `groundtruth of the request
             - 2. Filter the documents that do not have a corresponding groundtruth
             - 2. The BaseEvaluator works as if the `groundtruth` had been provided by the client as it comes in the request.

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
               workspace: $TEST_WORKDIR
           - !BaseEvaluator
             metas:
               name: evaluator  # a customized name
         metas:
           name: file_based_evaluator
           workspace: $TEST_WORKDIR

     Without defining any ``requests.on`` logic. When load from this YAML, it will be auto equipped with

     .. highlight:: yaml
     .. code-block:: yaml

         on:
           [SearchRequest, IndexRequest]:
             - !LoadGroundTruthDriver
               with:
                 executor: groundtruth_index
             - !BaseEvaluationDriver
               with:
                 executor: BaseKVIndexer
           ControlRequest:
             - !ControlReqDriver {}
     """
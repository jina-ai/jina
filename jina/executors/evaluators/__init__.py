__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable
from jina.proto import jina_pb2

from .. import BaseExecutor


class BaseEvaluator(BaseExecutor):
    """A :class:`BaseEvaluator` evaluates the content of matches against the expected GroundTruth.
    """

    def __init__(self, id_tag, *args, **kwargs):
        """"
        :param id_tag: the key in the tags of documents to identify uniquely a document
        """
        super().__init__(*args, **kwargs)
        self.id_tag = id_tag

    def evaluate(self, matches: Iterable[jina_pb2.Document],
                 groundtruth: Iterable[jina_pb2.Document], *args, **kwargs) -> float:
        """"
        :param matches: the matched documents from the request as matched by jina indexers and rankers
        :param groundtruth: the expected documents matches sorted as they are expected
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError

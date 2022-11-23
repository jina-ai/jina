from itertools import chain
from typing import Dict, List

from jina import Executor, requests, DocumentArray, Document


class ExecMerger(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)

    @requests
    def debug(self, docs_matrix: List[DocumentArray], **kwargs):
        self.logger.debug(
            f'Received doc matrix in exec-merger with length {len(docs_matrix)}.'
        )

        result = DocumentArray()
        for docs in zip(*docs_matrix):
            traversed_executors = [doc.tags['traversed-executors'] for doc in docs]
            shard_ids = [doc.tags['shard_id'] for doc in docs]
            shards = [doc.tags['shards'] for doc in docs]
            parallels = [doc.tags['parallel'] for doc in docs]
            traversed_executors = list(chain(*traversed_executors))
            doc = Document()
            doc.tags['traversed-executors'] = traversed_executors
            doc.tags['shard_id'] = shard_ids
            doc.tags['shards'] = shards
            doc.tags['parallel'] = parallels
            doc.tags['merged'] = True

            result.append(doc)

        return result

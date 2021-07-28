import base64
import sys
from collections import OrderedDict

from jina import Executor, requests, DocumentArray


class MatchMerger(Executor):
    @requests
    def merge(self, docs_matrix, **kwargs):
        results = OrderedDict()
        for docs in docs_matrix:
            for doc in docs:
                if doc.id in results:
                    results[doc.id].matches.extend(doc.matches)
                else:
                    results[doc.id] = doc
        return DocumentArray(list(results.values()))

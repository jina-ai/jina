# Match merger executor
from collections import OrderedDict

from jina import Executor, requests, DocumentArray


class MatchMerger(Executor):
    @requests
    def merge(self, docs_matrix, **kwargs):
        for doc_arr in docs_matrix:
            print(f'### Len Docs Array: {len(doc_arr)}')
            for doc in doc_arr:
                print(f'### Len DocArray Matches {doc.matches}')
        results = OrderedDict()
        for docs in docs_matrix:
            for doc in docs:
                if doc.id in results:
                    results[doc.id].matches.extend(doc.matches)
                else:
                    results[doc.id] = doc
        return DocumentArray(list(results.values()))

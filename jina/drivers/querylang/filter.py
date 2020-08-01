__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Any, Iterable

from .queryset.lookup import Q
from . import QueryLangDriver

if False:
    from ...proto import jina_pb2


class FilterQL(QueryLangDriver):
    def __init__(self, lookups: Dict[str, Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lookups = Q(**lookups) if lookups else None

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        if self.lookups:
            miss_idx = []
            for idx, doc in enumerate(docs):
                if not self.lookups.evaluate(doc):
                    miss_idx.append(idx)

            # delete non-exit matches in reverse
            for j in reversed(miss_idx):
                del docs[j]

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import QueryLangDriver

if False:
    from ...proto import jina_pb2


class ReverseQL(QueryLangDriver):
    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        prev_len = len(docs)
        for d in reversed(docs):
            dd = docs.add()
            dd.CopyFrom(d)
        del docs[:prev_len]

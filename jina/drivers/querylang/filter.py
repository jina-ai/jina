from typing import Dict, Any

from .queryset.lookup import _lookup
from .. import BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class FilterQL(BaseRecursiveDriver):
    def __init__(self, lookups: Dict[str, Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookups = lookups

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        if not all(_lookup(k, v, doc) for k, v in self.lookups.items()):
            del doc

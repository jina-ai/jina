from typing import Dict, Any

from .queryset.lookup import Q
from .. import BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class FilterQL(BaseRecursiveDriver):
    def __init__(self, lookups: Dict[str, Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookups = Q(**lookups) if lookups else None

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        if self.lookups and not self.lookups.evaluate(doc):
            del doc

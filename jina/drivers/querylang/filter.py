__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Any

from .queryset.lookup import Q
from .. import BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class FilterQL(BaseRecursiveDriver):
    def __init__(self, lookups: Dict[str, Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookups = Q(**lookups) if lookups else None

    def _postorder_apply(self, docs, *args, **kwargs):
        """often useful when you delete a recursive structure """

        def _traverse(_docs):
            if _docs:
                index_to_del = []
                for index, doc in enumerate(_docs):
                    if doc.level_depth < self._depth_end:
                        for r in self.traverse_fields:
                            _traverse(getattr(doc, r))
                    if doc.level_depth >= self._depth_start:
                        if self._apply(doc, *args, **kwargs):
                            index_to_del.append(index)

                for index in index_to_del:
                    del _docs[index]

                # check first doc if in the required depth range
                if _docs[0].level_depth >= self._depth_start:
                    self._apply_all(_docs, *args, **kwargs)

        _traverse(docs)

    def _preorder_apply(self, docs, *args, **kwargs):
        """often useful when you grow new structure, e.g. segment """

        def _traverse(_docs):
            if _docs:
                # check first doc if in the required depth range
                if _docs[0].level_depth >= self._depth_start:
                    self._apply_all(_docs, *args, **kwargs)

                index_to_del = []
                for index, doc in enumerate(_docs):
                    if doc.level_depth >= self._depth_start:
                        if self._apply(doc, *args, **kwargs):
                            index_to_del.append(index)
                    if doc.level_depth < self._depth_end:
                        for r in self.traverse_fields:
                            _traverse(getattr(doc, r))

                for index in index_to_del:
                    del _docs[index]

        _traverse(docs)

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        if self.lookups and not self.lookups.evaluate(doc):
            return True
        else:
            return False

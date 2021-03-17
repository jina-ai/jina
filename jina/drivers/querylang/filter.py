__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Any, Iterable

from ...types.querylang.queryset.lookup import Q
from .. import QuerySetReader, BaseRecursiveDriver, ContextAwareRecursiveMixin

if False:
    from ...types.sets import DocumentSet


class FilterQL(QuerySetReader, ContextAwareRecursiveMixin, BaseRecursiveDriver):
    """Filters incoming `docs` by evaluating a series of `lookup rules`.

    This is often useful when the proceeding Pods require only a signal, not the full message.

    Example ::
    - !FilterQL
        with:
            lookups: {modality: mode2}
    - !EncodeDriver
        with:
            method: encode

    ensures that the EncodeDriver will only get documents which modality field value is `mode2` by filtering
    those documents at the specific levels that do not comply with this condition

    :param lookups: (dict) a dictionary where keys are interpreted by ``:class:`LookupLeaf`` to form a
    an evaluation function. For instance, a dictionary ``{ modality__in: [mode1, mode2] }``, would create
    an evaluation function that will check if the field `modality` is found in `[mode1, mode2]`
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, lookups: Dict[str, Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lookups = lookups

    def _apply_all(
        self, doc_sequences: Iterable['DocumentSet'], *args, **kwargs
    ) -> None:
        for docs in doc_sequences:
            if self.lookups:
                _lookups = Q(**self.lookups)
                miss_idx = []
                for idx, doc in enumerate(docs):
                    if not _lookups.evaluate(doc):
                        miss_idx.append(idx)

                # delete non-exit matches in reverse
                for j in reversed(miss_idx):
                    del docs[j]

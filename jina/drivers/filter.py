__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseDriver


class TopKFilterDriver(BaseDriver):
    """Restrict the size of the ``topk_results`` to ``k`` (given by the request)

    This driver works on both chunk and doc level
    """

    def __call__(self, *args, **kwargs):
        # keep to topk docs
        for d in self.req.docs:
            del d.topk_results[self.req.top_k:]
            topk_doc_id = {md.match_doc.doc_id for md in d.topk_results}
            # keep only the chunks that hit the topk docs
            for c in d.chunks:
                # delete in reverse so that idx won't be messed up
                for idx, mc in reversed(list(enumerate(c.topk_results))):
                    if mc.match_chunk.doc_id not in topk_doc_id:
                        del c.topk_results[idx]

                # if it's still > k
                del c.topk_results[self.req.top_k:]


class TopKSortDriver(BaseDriver):
    """Sort the ``topk_results``

    This driver works on both chunk and doc level
    """

    def __init__(self, descending: bool = False, *args, **kwargs):
        """

        :param descending: sort the value from big to small
        """

        super().__init__(*args, **kwargs)
        self.descending = descending

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            d.topk_results.sort(key=lambda x: x.score.value, reverse=self.descending)
            for c in d.chunks:
                c.topk_results.sort(key=lambda x: x.score.value, reverse=self.descending)

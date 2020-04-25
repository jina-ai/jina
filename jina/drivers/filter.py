__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseDriver


class TopKFilterDriver(BaseDriver):
    """Restrict the size of the ``topk_results`` to ``k`` (given by the request)

    This driver works on both chunk and doc level
    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            _topk = [k for k in d.topk_results[:self.req.top_k]]
            d.ClearField('topk_results')
            d.topk_results.extend(_topk)
            for c in d.chunks:
                _topk = [k for k in c.topk_results[:self.req.top_k]]
                c.ClearField('topk_results')
                c.topk_results.extend(_topk)


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
            _sort = sorted(d.topk_results, key=lambda x: x.score.value, reverse=self.descending)
            d.ClearField('topk_results')
            d.topk_results.extend(_sort)
            for c in d.chunks:
                _sort = sorted(c.topk_results, key=lambda x: x.score.value, reverse=self.descending)
                c.ClearField('topk_results')
                c.topk_results.extend(_sort)

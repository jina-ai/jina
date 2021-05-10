from .base import BaseFlow
from ..clients.mixin import CRUDMixin, PostMixin


class Flow(PostMixin, CRUDMixin, BaseFlow):
    """The synchronous version of :class:`AsyncFlow`.

    For proper usage see `this guide` <https://docs.jina.ai/chapters/flow/index.html>
    """

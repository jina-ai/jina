from .base import BaseFlow
from ..clients.mixin import PostMixin


class Flow(PostMixin, BaseFlow):
    """The synchronous version of :class:`AsyncFlow`.

    For proper usage see `this guide` <https://docs.jina.ai/chapters/flow/index.html>
    """

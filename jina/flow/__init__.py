from .base import BaseFlow
from .mixin.crud import CRUDFlowMixin


class Flow(CRUDFlowMixin, BaseFlow):
    """The synchronous version of :class:`AsyncFlow`.

    For proper usage see `this guide` <https://docs.jina.ai/chapters/flow/index.html>
    """
    pass

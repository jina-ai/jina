from .base import BaseFlow
from .mixin.control import ControlFlowMixin
from .mixin.crud import CRUDFlowMixin


class Flow(CRUDFlowMixin, ControlFlowMixin, BaseFlow):
    """The synchronous version of :class:`AsyncFlow`.

    For proper usage see `this guide` <https://docs.jina.ai/chapters/flow/index.html>
    """

    pass

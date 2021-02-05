from .base import BaseFlow
from .mixin.crud import CRUDFlowMixin


class Flow(CRUDFlowMixin, BaseFlow):
    pass

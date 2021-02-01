from . import Request
from .mixin import *


class TrainRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    pass

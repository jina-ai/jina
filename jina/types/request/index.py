from . import Request
from .mixin import *


class IndexRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    pass

from . import Request
from .mixin import *


class SearchRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    pass

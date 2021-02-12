from . import Request
from .mixin import *


class IndexRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    """Index request class."""

    pass

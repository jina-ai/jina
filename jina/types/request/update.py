from . import Request
from .mixin import *


class UpdateRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    """Update request class."""

    pass

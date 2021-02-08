from . import Request
from .mixin import *


class UpdateRequest(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    pass

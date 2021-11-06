from abc import ABC

from .content import ContentPropertyMixin
from .empty import EmptyMixin
from .getattr import GetAttributeMixin
from .group import GroupMixin
from .io.binary import BinaryIOMixin
from .io.common import CommonIOMixin
from .io.csv import CsvIOMixin
from .io.json import JsonIOMixin
from .magic import MagicMixin
from .match import MatchMixin
from .plot import PlotMixin
from .sample import SampleMixin
from .text import TextToolsMixin
from .traverse import TraverseMixin


class AllMixins(
    GetAttributeMixin,
    ContentPropertyMixin,
    GroupMixin,
    EmptyMixin,
    MagicMixin,
    CsvIOMixin,
    JsonIOMixin,
    BinaryIOMixin,
    CommonIOMixin,
    MatchMixin,
    TraverseMixin,
    PlotMixin,
    SampleMixin,
    TextToolsMixin,
    ABC,
):
    """All plugins that can be used in DA/DAM"""

    ...

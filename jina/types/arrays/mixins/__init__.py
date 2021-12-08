from abc import ABC

from .content import ContentPropertyMixin
from .empty import EmptyMixin
from .evaluation import EvaluationMixin
from .getattr import GetAttributeMixin
from .group import GroupMixin
from .io.binary import BinaryIOMixin
from .io.common import CommonIOMixin
from .io.csv import CsvIOMixin
from .io.json import JsonIOMixin
from .io.from_gen import FromGeneratorMixin
from .magic import MagicMixin
from .match import MatchMixin
from .plot import PlotMixin
from .sample import SampleMixin
from .text import TextToolsMixin
from .traverse import TraverseMixin
from .embed import EmbedMixin
from .parallel import ParallelMixin
from .io.dataframe import DataframeIOMixin


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
    EmbedMixin,
    FromGeneratorMixin,
    MatchMixin,
    TraverseMixin,
    PlotMixin,
    SampleMixin,
    TextToolsMixin,
    EvaluationMixin,
    ParallelMixin,
    DataframeIOMixin,
    ABC,
):
    """All plugins that can be used in :class:`DocumentArray` or :class:`DocumentArrayMemmap`. """

    ...

from abc import ABC

from .content import ContentPropertyMixin
from .embed import EmbedMixin
from .empty import EmptyMixin
from .evaluation import EvaluationMixin
from .getattr import GetAttributeMixin
from .group import GroupMixin
from .io.binary import BinaryIOMixin
from .io.common import CommonIOMixin
from .io.csv import CsvIOMixin
from .io.dataframe import DataframeIOMixin
from .io.from_gen import FromGeneratorMixin
from .io.json import JsonIOMixin
from .io.pushpull import PushPullMixin
from .magic import MagicMixin
from .match import MatchMixin
from .parallel import ParallelMixin
from .plot import PlotMixin
from .reduce import ReduceMixin
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
    EmbedMixin,
    PushPullMixin,
    FromGeneratorMixin,
    MatchMixin,
    TraverseMixin,
    PlotMixin,
    SampleMixin,
    TextToolsMixin,
    EvaluationMixin,
    ReduceMixin,
    ParallelMixin,
    DataframeIOMixin,
    ABC,
):
    """All plugins that can be used in :class:`DocumentArray` or :class:`DocumentArrayMemmap`. """

    ...

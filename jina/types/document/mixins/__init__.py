from .attribute import GetSetAttributeMixin
from .audio import AudioDataMixin
from .buffer import BufferDataMixin
from .content import ContentPropertyMixin
from .convert import ConvertMixin
from .dump import DumpFileMixin
from .image import ImageDataMixin
from .sugar import SingletonSugarMixin
from .mesh import MeshDataMixin
from .plot import PlotMixin
from .text import TextDataMixin
from .version import VersionedMixin
from .video import VideoDataMixin


class AllMixins(
    ContentPropertyMixin,
    ConvertMixin,
    AudioDataMixin,
    ImageDataMixin,
    TextDataMixin,
    MeshDataMixin,
    VideoDataMixin,
    BufferDataMixin,
    PlotMixin,
    DumpFileMixin,
    VersionedMixin,
    SingletonSugarMixin,
    GetSetAttributeMixin,
):
    """All plugins that can be used in :class:`Document`. """

    ...

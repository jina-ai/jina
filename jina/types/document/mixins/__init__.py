from .audio import AudioDataMixin
from .content import ContentPropertyMixin
from .convert import ConvertMixin
from .dump import DumpFileMixin
from .attribute import GetSetAttributeMixin
from .image import ImageDataMixin
from .mesh import MeshDataMixin
from .plot import PlotMixin
from .text import TextDataMixin
from .video import VideoDataMixin
from .version import VersionedMixin
from .buffer import BufferDataMixin


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
    GetSetAttributeMixin,
):
    """All plugins that can be used in :class:`Document`. """

    ...

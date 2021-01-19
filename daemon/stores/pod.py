from jina.peapods import Pod
from .pea import PeaStore


class PodStore(PeaStore):
    peapod_cls = Pod

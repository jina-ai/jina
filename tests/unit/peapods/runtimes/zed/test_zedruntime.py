from jina.parser import set_pea_parser
from jina.peapods.peas.base import BasePea
from jina.peapods.runtimes.zed import ZEDRuntime


def test_zed_runtime():
    arg = set_pea_parser().parse_args([])
    with BasePea(arg):
        pass
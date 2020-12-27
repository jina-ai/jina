from jina.parser import set_pea_parser, set_gateway_parser
from jina.peapods.peas.base import BasePea


def test_zed_runtime():
    arg = set_pea_parser().parse_args([])
    with BasePea(arg):
        pass


def test_grpc_runtime():
    arg = set_gateway_parser().parse_args([])
    with BasePea(arg):
        pass

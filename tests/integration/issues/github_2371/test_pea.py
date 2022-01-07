from jina.parsers import set_pea_parser
from jina.peapods.peas.factory import PeaFactory


def test_pea_instantiate_start_same_context():
    arg = set_pea_parser().parse_args([])
    peas_args = [arg, arg]

    for args in peas_args:
        pea = PeaFactory.build_pea(args)
        with pea:
            pass


def test_pea_instantiate_start_different_context():
    arg = set_pea_parser().parse_args([])
    peas_args = [arg, arg]
    peas = []
    for args in peas_args:
        peas.append(PeaFactory.build_pea(args))

    for pea in peas:
        with pea:
            pass

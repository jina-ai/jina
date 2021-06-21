from jina.parsers import set_pea_parser
from jina.peapods import Pea


def test_pea_instantiate_start_same_context():
    arg = set_pea_parser().parse_args([])
    peas_args = [arg, arg]

    for args in peas_args:
        pea = Pea(args)
        with pea:
            pass


def test_pea_instantiate_start_different_context():
    arg = set_pea_parser().parse_args([])
    peas_args = [arg, arg]
    peas = []
    for args in peas_args:
        peas.append(Pea(args))

    for pea in peas:
        with pea:
            pass

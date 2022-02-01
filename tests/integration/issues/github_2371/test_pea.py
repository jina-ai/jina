from jina.parsers import set_pod_parser
from jina.orchestrate.pods.factory import PodFactory


def test_pod_instantiate_start_same_context():
    arg = set_pod_parser().parse_args([])
    peas_args = [arg, arg]

    for args in peas_args:
        pod = PodFactory.build_pod(args)
        with pod:
            pass


def test_pod_instantiate_start_different_context():
    arg = set_pod_parser().parse_args([])
    peas_args = [arg, arg]
    peas = []
    for args in peas_args:
        peas.append(PodFactory.build_pod(args))

    for pod in peas:
        with pod:
            pass

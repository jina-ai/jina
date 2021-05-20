from jina.parsers import set_pod_parser
from jina.peapods.pods import Pod
from jina.peapods.pods.compound import CompoundPod
from jina.peapods.pods.factory import PodFactory


def test_pod_factory_pod():
    args_no_replicas = set_pod_parser().parse_args(['--replicas', '1'])
    assert isinstance(PodFactory.build_pod(args_no_replicas), Pod)

    args_replicas = set_pod_parser().parse_args(['--replicas', '2'])
    assert isinstance(PodFactory.build_pod(args_replicas), CompoundPod)

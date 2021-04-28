from jina.peapods.pods.factory import PodFactory
from jina.peapods.pods import Pod
from jina.peapods.pods.compoundpod import CompoundPod
from jina.parsers import set_pod_parser


def test_pod_factory_pod():
    args_no_replicas = set_pod_parser().parse_args(['--replicas', '1'])
    assert isinstance(PodFactory.build_pod(args_no_replicas), Pod)

    args_replicas = set_pod_parser().parse_args(['--replicas', '2'])
    assert isinstance(PodFactory.build_pod(args_replicas), CompoundPod)

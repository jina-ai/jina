from jina.enums import InfrastructureType
from jina.parsers import set_pod_parser
from jina.peapods.pods import Pod
from jina.peapods.pods.compound import CompoundPod
from jina.peapods.pods.factory import PodFactory
from jina.peapods.pods.k8s import K8sPod


def test_pod_factory_pod():
    args_no_replicas = set_pod_parser().parse_args(['--shards', '1'])
    assert isinstance(PodFactory.build_pod(args_no_replicas), Pod)

    args_replicas = set_pod_parser().parse_args(['--shards', '2'])
    assert isinstance(PodFactory.build_pod(args_replicas), CompoundPod)

    args_no_replicas = set_pod_parser().parse_args(['--replicas', '2'])
    assert isinstance(PodFactory.build_pod(args_no_replicas), Pod)


def test_pod_factory_k8s():
    args_replicas = set_pod_parser().parse_args([])
    assert isinstance(
        PodFactory.build_pod(args_replicas, infrastructure=InfrastructureType.K8S),
        K8sPod,
    )

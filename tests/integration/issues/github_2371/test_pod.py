from jina.orchestrate.pods.factory import PodFactory
from tests.helper import _generate_pod_args


def test_pod_instantiate_start_same_context():
    arg = _generate_pod_args()
    pod_args = [arg, arg]

    for args in pod_args:
        pod = PodFactory.build_pod(args)
        with pod:
            pass


def test_pod_instantiate_start_different_context():
    arg = _generate_pod_args()
    pod_args = [arg, arg]
    pods = []
    for args in pod_args:
        pods.append(PodFactory.build_pod(args))

    for pod in pods:
        with pod:
            pass

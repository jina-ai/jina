from daemon.models import PodModel, RawPodModel


def test_single_no_exceptions():
    PodModel()
    # this gets executed while verifying inputs
    PodModel().dict()
    # this gets executed while creating docs
    PodModel().schema()


def test_parallel_no_exceptions():
    RawPodModel()
    # this gets executed while verifying inputs
    RawPodModel().dict()
    # this gets executed while creating docs
    RawPodModel().schema()

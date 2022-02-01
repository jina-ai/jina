from daemon.models import PodModel


def test_no_exceptions():
    PodModel()
    # this gets executed while verifying inputs
    PodModel().dict()
    # this gets executed while creating docs
    PodModel().schema()

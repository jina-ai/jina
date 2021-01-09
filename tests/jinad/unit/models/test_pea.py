from daemon.models import PeaModel


def test_no_exceptions():
    PeaModel()
    # this gets executed while verifying inputs
    PeaModel().dict()
    # this gets executed while creating docs
    PeaModel().schema()

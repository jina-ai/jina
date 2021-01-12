from daemon.models import FlowModel


def test_no_exceptions():
    FlowModel()
    # this gets executed while verifying inputs
    FlowModel().dict()
    # this gets executed while creating docs
    FlowModel().schema()

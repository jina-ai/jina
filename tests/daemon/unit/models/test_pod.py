from daemon.models import DeploymentModel


def test_single_no_exceptions():
    DeploymentModel()
    # this gets executed while verifying inputs
    DeploymentModel().dict()
    # this gets executed while creating docs
    DeploymentModel().schema()

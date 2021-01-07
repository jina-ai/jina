from daemon.models import SinglePodModel, ParallelPodModel


def test_single_no_exceptions():
    SinglePodModel()
    # this gets executed while verifying inputs
    SinglePodModel().dict()
    # this gets executed while creating docs
    SinglePodModel().schema()


def test_parallel_no_exceptions():
    ParallelPodModel()
    # this gets executed while verifying inputs
    ParallelPodModel().dict()
    # this gets executed while creating docs
    ParallelPodModel().schema()

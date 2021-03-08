import os

from jina.optimizers.flow_runner import SingleFlowRunner
from tests import random_docs, validate_callback


def test_flow_runner(tmpdir, mocker):
    def callback(resp):
        if len(resp.search.docs):
            assert True
        else:
            assert False

    workspace = os.path.join(tmpdir, 'test_flow_runner')

    flow_runner = SingleFlowRunner(
        flow_yaml='flow.yml',
        documents=random_docs(5),
        request_size=1,
        execution_method='index',
        overwrite_workspace=True,
    )

    flow_runner.run(
        workspace=workspace,
        trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace},
    )
    # Test overwriting
    flow_runner.run(
        workspace=workspace,
        trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace},
    )

    flow_runner = SingleFlowRunner(
        flow_yaml='flow.yml',
        documents=random_docs(5),
        request_size=1,
        execution_method='search',
    )

    mock = mocker.Mock()
    flow_runner.run(
        workspace=workspace,
        trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace},
        callback=mock,
    )

    validate_callback(mock, callback)
    assert os.path.exists(os.path.join(workspace, 'tmp2'))

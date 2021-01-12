import os
import pytest

from jina.optimizers.flow_runner import FlowRunner
from tests import random_docs


def test_flow_runner(tmpdir, mocker):
    m = mocker.Mock()

    def callback(resp):
        m()
        if len(resp.search.docs):
            assert True
        else:
            assert False

    workspace = os.path.join(tmpdir, 'test_flow_runner')

    flow_runner = FlowRunner(
        flow_yaml='flow.yml',
        documents=random_docs(5),
        batch_size=1,
        task='index',
        overwrite_workspace=True,
    )

    flow_runner.run(workspace=workspace, trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace})
    # Test overwriting
    flow_runner.run(workspace=workspace, trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace})

    flow_runner = FlowRunner(
        flow_yaml='flow.yml',
        documents=random_docs(5),
        batch_size=1,
        task='search',
        callback=callback
    )

    flow_runner.run(workspace=workspace, trial_parameters={'JINA_TEST_FLOW_RUNNER_WORKSPACE': workspace})

    m.assert_called()
    assert os.path.exists(os.path.join(workspace, 'tmp2'))


def test_wrong_task():
    with pytest.raises(ValueError) as excinfo:
        _ = FlowRunner(
            flow_yaml='flow.yml',
            documents=random_docs(5),
            batch_size=1,
            task='query',
        )
        assert 'task can be either of index or search' == str(excinfo.value)

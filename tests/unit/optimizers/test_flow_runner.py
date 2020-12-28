from pathlib import Path

from jina.optimizers.flow_runner import FlowRunner
from tests import random_docs

import pytest

cur_dir = Path(__file__).parent

def test_flow_runner(tmpdir, mocker):
    m = mocker.Mock()

    def callback(resp):
        m()
        if len(resp.search.docs):
            assert True
        else:
            assert False

    flow_runner = FlowRunner(
        flow_yaml=cur_dir/'flow.yml',
        documents=random_docs(5),
        batch_size=1,
        task='index',
        overwrite_workspace=True,
    )

    flow_runner.run(workspace=tmpdir)

    flow_runner = FlowRunner(
        flow_yaml=cur_dir/'flow.yml',
        documents=random_docs(5),
        batch_size=1,
        task='search',
        callback=callback
    )

    flow_runner.run(workspace=tmpdir)
    
    m.assert_called()
    assert Path(tmpdir/'flows'/'flow.yml').exists()

def test_wrong_task():

    with pytest.raises(ValueError) as excinfo:
        _ = FlowRunner(
        flow_yaml=cur_dir/'flow.yml',
        documents=random_docs(5),
        batch_size=1,
        task='query',
    )
        assert 'task can be either of index or search' == str(excinfo.value)
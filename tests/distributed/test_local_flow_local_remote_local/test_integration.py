import os

import pytest

from jina import Document
from jina import Flow
from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
@pytest.mark.parametrize(
    'encoder_needs, indexer_needs, indexer_method',
    [('crafter', 'encoder', 'add'), ('gateway', '[encoder, crafter]', 'needs')],
)
def test_flow(
    docker_compose, tmpdir, mocker, encoder_needs, indexer_needs, indexer_method
):
    text = 'cats rules'

    def validate_output(resp):
        assert len(resp.data.docs) == 1
        assert resp.data.docs[0].text == text

    os.environ['JINA_ENCODER_HOST'] = '172.28.1.1'
    os.environ['JINA_WORKSPACE'] = str(tmpdir)
    os.environ['JINA_ENCODER_NEEDS'] = encoder_needs
    os.environ['JINA_INDEXER_NEEDS'] = indexer_needs
    os.environ['JINA_INDEXER_METHOD'] = indexer_method

    with Document() as doc:
        doc.content = text

    mock = mocker.Mock()
    with Flow.load_config(flow_yml) as f:
        f.index([doc], on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_output)

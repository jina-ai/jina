import os
import pytest

from jina import Flow, Document
from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_override_config_params(mocker):
    def validate_response(resp):
        doc = resp.docs[0]
        assert doc.tags['param1'] == 50
        assert doc.tags['param2'] == 30
        assert doc.tags['param3'] == 10  # not overriden
        assert doc.tags['name'] == 'name'  # not override
        assert doc.tags['workspace'] == 'different_workspace'

    mock = mocker.Mock()
    f = Flow().add(
        uses=os.path.join(cur_dir, 'default_config.yml'),
        override_with_params={'param1': 50, 'param2': 30},
        override_metas_params={'workspace': 'different_workspace'},
    )
    with f:
        f.search(inputs=[Document()], on_done=mock)
    validate_callback(mock, validate_response)

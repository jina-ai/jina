import pytest
from jina.executors.encoders.frameworks import BaseOnnxEncoder
from jina.excepts import ModelCheckpointNotExist


def test_raised_exception():
    with pytest.raises(ModelCheckpointNotExist):
        BaseOnnxEncoder()

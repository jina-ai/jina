import pytest

from jina.excepts import ModelCheckpointNotExist
from jina.executors.encoders.frameworks import BaseOnnxEncoder


def test_raised_exception():
    with pytest.raises(ModelCheckpointNotExist):
        BaseOnnxEncoder()

import pytest
from jina.executors.encoders.frameworks import BaseOnnxEncoder
from jina.excepts import PretrainedModelFileDoesNotExist


def test_raised_exception():
    with pytest.raises(PretrainedModelFileDoesNotExist):
        BaseOnnxEncoder()

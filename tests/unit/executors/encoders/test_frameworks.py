import pytest

from jina.excepts import ModelCheckpointNotExist
from jina.executors.encoders.frameworks import BaseOnnxEncoder, BaseMindsporeEncoder


def test_raised_exception():
    with pytest.raises(ModelCheckpointNotExist):
        BaseOnnxEncoder()

    with pytest.raises(ModelCheckpointNotExist):
        BaseMindsporeEncoder()

    with pytest.raises(AttributeError):
        BaseMindsporeEncoder.model()


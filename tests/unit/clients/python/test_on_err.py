import numpy as np
import pytest
from google.protobuf.pyext._message import RepeatedCompositeContainer

from jina.excepts import BadClientCallback
from jina.flow import Flow
from jina.proto import jina_pb2


@pytest.mark.parametrize('cb_on, x_type', [('DOCS', RepeatedCompositeContainer),
                                           ('GROUNDTRUTHS', RepeatedCompositeContainer),
                                           ('REQUEST', jina_pb2.Request),
                                           ('BODY', jina_pb2.Request.IndexRequest),
                                           ])
def test_diff_field(cb_on, x_type):
    def validate(x):
        assert isinstance(x, x_type)

    f = Flow().add()

    with f:
        f.index_ndarray(np.random.random([5, 4]),
                        output_fn=validate, callback_on=cb_on)


def test_on_error():
    def validate(x):
        raise NotImplementedError

    f = Flow().add()

    with pytest.raises(BadClientCallback), f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=False)

    with f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=True)

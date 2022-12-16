from datetime import datetime
import pytest

from jina import Document, DocumentArray, Flow


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_invalid_input_raise(protocol):
    f = Flow(protocol=protocol).add()

    with pytest.raises(BaseException):
        with f:
            da = DocumentArray([Document(text='hello', tags={'date': datetime.now()})])
            f.post(on='/', inputs=da)  # process should stop here and raise an exception

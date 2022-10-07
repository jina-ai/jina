import pytest
from datetime import datetime
from jina import Flow, DocumentArray, Document


class MyOwnException(Exception):
    pass


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_invalid_input_raise(protocol):
    f = Flow(protocol=protocol).add()

    try:
        with f:
            da = DocumentArray([Document(text='hello', tags={'date': datetime.now()})])
            try:
                f.post(on='/', inputs=da)  # process should stop here and raise an exception
            except:
                raise MyOwnException
            assert False
    except MyOwnException:
        pass
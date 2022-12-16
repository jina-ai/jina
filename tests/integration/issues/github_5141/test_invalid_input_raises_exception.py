from datetime import datetime

import pytest

from docarray import Document, DocumentArray, Flow


class MyOwnException(Exception):
    pass


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_invalid_input_raise(protocol):
    f = Flow(protocol=protocol).add()

    try:
        with f:
            da = DocumentArray([Document(text='hello', tags={'date': datetime.now()})])
            try:
                f.post(
                    on='/', inputs=da
                )  # process should stop here and raise an exception
            except Exception:
                raise MyOwnException
            assert False
    except MyOwnException:
        pass

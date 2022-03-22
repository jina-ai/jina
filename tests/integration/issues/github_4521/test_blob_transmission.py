import pytest
from docarray import Document

from jina import Client, Executor, Flow, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, parameters, **kwargs):
        decode = parameters['decode']
        if decode:
            docs[0].text = docs[0].blob.decode('UTF-8')


@pytest.mark.parametrize('decode', [True, False])
@pytest.mark.parametrize('protocol', ['grpc', 'websocket', 'http'])
def test_blob_transmission(decode, protocol):
    decode = False
    f = Flow(protocol=protocol).add(uses=MyExec)
    with f:
        c = Client(port=f.port, protocol=protocol)
        d = c.post('/', Document(blob=b'hello'), parameters={'decode': decode})[0]
    if decode:  # test that the Executor gets the correct data
        assert d.text == 'hello'
    else:  # test that the response contains the correct data
        assert d.blob == b'hello'

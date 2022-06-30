from docarray import Document, DocumentArray

from jina import Client


def test_new_client_old_proto():  # need to build and start old server docker
    client = Client(port=8080)

    client.index(DocumentArray([Document(text='hello') for _ in range(10)]))

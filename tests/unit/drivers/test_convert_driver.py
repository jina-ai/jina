import numpy as np
from PIL import Image
import pytest

from jina.drivers.convert import Blob2PngURI
from jina.drivers.helper import array2pb
from jina.proto import jina_pb2


def create_document(arr_size):
    doc = jina_pb2.Document()
    doc.blob.CopyFrom(array2pb(np.random.randint(0, 255, arr_size)))
    return doc


docs = [create_document([32*28]), create_document([32, 28]), create_document([32, 28, 3])]
modes = ['L', 'L', 'RGB']
test_data = zip(docs, modes)


@pytest.mark.parametrize('data', test_data)
def test_blob2pnguri_driver(data):
    doc, mode = data
    width, height = 28, 32

    driver = Blob2PngURI(target='uri', width=width, height=height)
    driver._apply(doc)
    Image.frombytes(mode, (width, height), doc.uri.encode()) # just to check if the data is enough for the image recreation
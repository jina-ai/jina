import os

import numpy as np
import pytest
from jina.drivers.convert import (Blob2PngURI, Buffer2URI, URI2Buffer,
                                  URI2DataURI)
from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray
from PIL import Image


def create_document(arr_size):
    doc = jina_pb2.DocumentProto()
    NdArray(doc.blob).value = np.random.randint(0, 255, arr_size)
    return doc


test_arrays = ([32 * 28], [32, 28], [32, 28, 3])
docs = [create_document(arr) for arr in test_arrays]
modes = ['L', 'L', 'RGB']
@pytest.mark.parametrize('data', zip(docs, modes))
def test_blob2pnguri_driver(data):
    doc, mode = data
    width, height = 28, 32

    driver = Blob2PngURI(target='uri', width=width, height=height)
    driver._apply_all([doc])
    Image.frombytes(mode, (width, height),
                    doc.uri.encode())  # just to check if the data is enough for the image recreation


uris = ['https://jina.ai/', 'http://jina.ai/',
        f'./{os.path.basename(__file__)}']
@pytest.mark.parametrize('data', uris)
def test_uri2buffer_driver(data):
    doc = jina_pb2.DocumentProto()
    initialized_buffer = doc.buffer
    doc.uri = data
    driver = URI2Buffer(target='buffer')
    driver.convert(doc)
    converted_buffer = doc.buffer
    assert initialized_buffer != converted_buffer


@pytest.mark.parametrize('data', uris)
def test_uri2datauri_driver(data):
    doc = jina_pb2.DocumentProto()
    initialized_uri = doc.uri
    doc.uri = data
    driver = URI2DataURI(target='uri')
    driver.convert(doc)
    converted_datauri = doc.uri
    assert initialized_uri != converted_datauri


buffers = [b'', b'randombuffer', bytes(8)]
@pytest.mark.parametrize('data', buffers)
def test_buffer2uri_driver(data):
    doc = jina_pb2.DocumentProto()
    initialized_uri = doc.uri
    doc.buffer = data
    driver = Buffer2URI(target='uri')
    driver.convert(doc)
    converted_datauri = doc.uri
    assert initialized_uri != converted_datauri

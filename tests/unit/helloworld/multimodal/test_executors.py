import os

import pytest
from PIL import Image

from jina import Document, DocumentArray, Flow
from jina.helloworld.multimodal.executors import Segmenter


@pytest.fixture(scope='function')
def segmenter_doc_array():
    inputs = [
        Document(tags={'caption': 'hello', 'image': '1.png'}),
        Document(tags={'caption': 'world', 'image': '2.png'}),
    ]
    return DocumentArray(inputs)


def create_test_img(path, file_name):
    img_path = path + '/people-img/'
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image.save(img_path + file_name, 'png')


def test_segmenter(segmenter_doc_array, tmpdir):
    def validate(resp):
        assert len(resp.data.docs) == 2
        for doc in resp.data.docs:
            assert len(doc.chunks) == 2
            assert doc.chunks[0].mime_type == 'text/plain'
            assert doc.chunks[1].mime_type == 'image/jpeg'
            assert doc.uri.startswith('data')

    create_test_img(path=str(tmpdir), file_name='1.png')
    create_test_img(path=str(tmpdir), file_name='2.png')
    with Flow().add(uses=Segmenter) as f:
        f.index(inputs=segmenter_doc_array, on_done=validate)

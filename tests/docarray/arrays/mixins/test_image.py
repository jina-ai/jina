import io
from http.client import RemoteDisconnected
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from docarray import Document


@pytest.fixture
def fake_response():
    class FakeResponse:
        status: int
        data: bytes

        def __init__(self, *, data, status, num_fails):
            self.data = data
            self.status = status
            self.num_fails = num_fails
            self.current_fails = 0

        def read(self):
            if self.current_fails < self.num_fails:
                self.current_fails += 1
                raise RemoteDisconnected()
            return self.data

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return FakeResponse


@pytest.fixture
def image_blob():
    return np.array(Image.new('RGB', (5, 5)))


@pytest.fixture
def image_bytes():
    pil_img = Image.new('RGB', (5, 5))
    with io.BytesIO() as output:
        pil_img.save(output, format="png")
        return output.getvalue()


def urllib_patch(num_fails, fake_response, image_bytes):
    return patch(
        'urllib.request.urlopen',
        return_value=fake_response(
            data=bytes(image_bytes), status=200, num_fails=num_fails
        ),
    )


def test_default(fake_response, image_bytes, image_blob):
    with urllib_patch(0, fake_response, image_bytes):
        d = Document(uri='http://test-uri').load_uri_to_image_blob()
        assert np.alltrue(d.blob == image_blob)


@pytest.mark.parametrize('num_tries,num_fails', [(1, 0), (2, 1), (3, 2)])
@pytest.mark.parametrize('retry_sleep', [0, 1])
def test_uri_to_image_blob_success(
    fake_response, image_bytes, image_blob, num_tries, num_fails, retry_sleep
):
    with urllib_patch(num_fails, fake_response, image_bytes):
        d = Document(uri='http://test-uri').load_uri_to_image_blob(
            tries=num_tries, retry_sleep=retry_sleep
        )
        assert np.alltrue(d.blob == image_blob)


@pytest.mark.parametrize('num_tries,num_fails', [(1, 1), (2, 2), (2, 3)])
def test_uri_to_image_blob_fail(
    fake_response, image_bytes, image_blob, num_tries, num_fails
):
    with pytest.raises(Exception):
        with urllib_patch(num_fails, fake_response, image_bytes):
            Document(uri='http://test-uri').load_uri_to_image_blob(tries=num_tries)

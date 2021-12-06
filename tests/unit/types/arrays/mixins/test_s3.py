import os
import uuid

import numpy as np
import pytest

from jina import DocumentArray
from jina.excepts import InvalidS3URL
from jina.types.arrays.mixins.io.s3 import S3URL
from tests import random_docs


def aws_envs_not_set():
    return (
        'AWS_ACCESS_KEY_ID' not in os.environ
        or 'AWS_SECRET_ACCESS_KEY' not in os.environ
    )


@pytest.fixture
def s3_url():
    s3_url = S3URL(f's3://jina-core-ci/d1/{str(uuid.uuid4())}')
    yield s3_url
    s3_url.delete()


@pytest.mark.parametrize(
    'url, bucket, key',
    [
        ('s3://abc/dir1/dir2/a.txt', 'abc', 'dir1/dir2/a.txt'),
        ('s3://blah/a.bin', 'blah', 'a.bin'),
    ],
)
def test_good_s3_url(url, bucket, key):
    s3_url = S3URL(url)
    assert s3_url.bucket == bucket
    assert s3_url.key == key


@pytest.mark.parametrize(
    'url',
    ['http://abc.com/blah', 'https://blah.com/a'],
)
def test_bad_s3_url(url):
    with pytest.raises(InvalidS3URL):
        S3URL(url)


@pytest.mark.skipif(
    condition=aws_envs_not_set(), reason='AWS creds not set as env vars'
)
def test_da_binary_save_load_s3(s3_url):
    da = DocumentArray(random_docs(100))
    da.save_binary(s3_url)
    loaded_doc = DocumentArray.load_binary(s3_url)
    assert type(da) is type(loaded_doc)
    assert len(da) == len(loaded_doc)
    for d, d_r in zip(da, loaded_doc):
        assert d.id == d_r.id
        np.testing.assert_equal(d.embedding, d_r.embedding)
        assert d.content == d_r.content


@pytest.mark.skipif(
    condition=aws_envs_not_set(), reason='AWS creds not set as env vars'
)
def test_da_json_save_load_s3(s3_url):
    da = DocumentArray(random_docs(100))
    da.save_json(s3_url)
    loaded_doc = DocumentArray.load_json(s3_url)
    assert type(da) is type(loaded_doc)
    assert len(da) == len(loaded_doc)
    for d, d_r in zip(da, loaded_doc):
        assert d.id == d_r.id
        np.testing.assert_equal(d.embedding, d_r.embedding)
        assert d.content == d_r.content

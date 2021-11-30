import os

import numpy as np
import pytest

from jina import DocumentArray, DocumentArrayMemmap
from jina.logging.profile import TimeContext
from tests import random_docs


def da_and_dam():
    da = DocumentArray(random_docs(100))
    dam = DocumentArrayMemmap()
    dam.extend(da)
    return da, dam


@pytest.mark.slow
@pytest.mark.parametrize('method', ['json', 'binary'])
@pytest.mark.parametrize('da', da_and_dam())
def test_document_save_load(method, tmp_path, da):
    tmp_file = os.path.join(tmp_path, 'test')
    with TimeContext(f'w/{method}'):
        da.save(tmp_file, file_format=method)
    with TimeContext(f'r/{method}'):
        da_r = type(da).load(tmp_file, file_format=method)

    assert type(da) is type(da_r)
    assert len(da) == len(da_r)
    for d, d_r in zip(da, da_r):
        assert d.id == d_r.id
        np.testing.assert_equal(d.embedding, d_r.embedding)
        assert d.content == d_r.content


@pytest.mark.parametrize('flatten_tags', [True, False])
@pytest.mark.parametrize('da', da_and_dam())
def test_da_csv_write(flatten_tags, tmp_path, da):
    tmpfile = os.path.join(tmp_path, 'test.csv')
    da.save_csv(tmpfile, flatten_tags)
    with open(tmpfile) as fp:
        assert len([v for v in fp]) == len(da) + 1


@pytest.mark.parametrize('da', [DocumentArray, DocumentArrayMemmap])
def test_from_ndarray(da):
    _da = da.from_ndarray(np.random.random([10, 256]))
    assert len(_da) == 10


@pytest.mark.parametrize('da', [DocumentArray, DocumentArrayMemmap])
def test_from_files(da):
    _da = da.from_files(patterns='*.*', to_dataturi=True, size=10)
    assert len(_da) == 10


cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('da', [DocumentArray, DocumentArrayMemmap])
def test_from_ndjson(da):
    with open(os.path.join(cur_dir, 'docs.jsonlines')) as fp:
        _da = da.from_ndjson(fp)
        assert len(_da) == 2

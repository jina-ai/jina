import gc
import multiprocessing

import pytest

from jina import DocumentArray, Document, DocumentArrayMemmap


@pytest.fixture(autouse=True)
def gc_collect():
    gc.collect()


def foo(d: Document):
    return d.load_uri_to_image_blob()


def foo_batch(da: DocumentArray):
    for d in da:
        foo(d)
    return da


@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.parametrize('backend', ['process', 'thread'])
@pytest.mark.parametrize('num_worker', [1, 2, None])
def test_parallel_map(pytestconfig, da_cls, backend, num_worker):
    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    # use a generator
    for d in da.map(foo, backend, num_worker=num_worker):
        pass

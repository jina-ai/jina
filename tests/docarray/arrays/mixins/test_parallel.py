import os
import pytest

from docarray import DocumentArray, Document, DocumentArrayMemmap


def foo(d: Document):
    return (
        d.load_uri_to_image_blob()
        .set_image_blob_normalization()
        .set_image_blob_channel_axis(-1, 0)
        .set_image_blob_shape((222, 222), 0)
    )


def foo_batch(da: DocumentArray):
    for d in da:
        foo(d)
    return da


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='this test somehow fail on Github CI, but it MUST run successfully on local',
)
@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.parametrize('backend', ['process', 'thread'])
@pytest.mark.parametrize('num_worker', [1, 2, None])
def test_parallel_map(pytestconfig, da_cls, backend, num_worker):
    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    # use a generator
    for d in da.map(foo, backend, num_worker=num_worker):
        assert d.blob.shape == (3, 222, 222)

    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    # use as list, here the caveat is when using process backend you can not modify thing in-place
    list(da.map(foo, backend, num_worker=num_worker))
    if backend == 'thread':
        assert da.blobs.shape == (len(da), 3, 222, 222)
    else:
        assert da.blobs is None

    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]
    da_new = da.apply(foo)
    assert da_new.blobs.shape == (len(da_new), 3, 222, 222)


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='this test somehow fail on Github CI, but it MUST run successfully on local',
)
@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
@pytest.mark.parametrize('backend', ['thread'])
@pytest.mark.parametrize('num_worker', [1, 2, None])
@pytest.mark.parametrize('b_size', [1, 2, 256])
def test_parallel_map_batch(pytestconfig, da_cls, backend, num_worker, b_size):
    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    # use a generator
    for _da in da.map_batch(
        foo_batch, batch_size=b_size, backend=backend, num_worker=num_worker
    ):
        for d in _da:
            assert d.blob.shape == (3, 222, 222)

    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    # use as list, here the caveat is when using process backend you can not modify thing in-place
    list(
        da.map_batch(
            foo_batch, batch_size=b_size, backend=backend, num_worker=num_worker
        )
    )
    if backend == 'thread':
        assert da.blobs.shape == (len(da), 3, 222, 222)
    else:
        assert da.blobs is None

    da_new = da.apply_batch(foo_batch, batch_size=b_size)
    assert da_new.blobs.shape == (len(da_new), 3, 222, 222)


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='this test somehow fail on Github CI, but it MUST run successfully on local',
)
@pytest.mark.parametrize('da_cls', [DocumentArray, DocumentArrayMemmap])
def test_map_lambda(pytestconfig, da_cls):
    da = da_cls.from_files(f'{pytestconfig.rootdir}/docs/**/*.png')[:10]

    for d in da:
        assert d.blob is None

    for d in da.map(lambda x: x.load_uri_to_image_blob()):
        assert d.blob is not None

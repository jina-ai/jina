import pytest

from jina import DocumentArrayMemmap, DocumentArray, Document


def foo(d: Document):
    return (
        d.load_uri_to_image_blob()
        .set_image_blob_normalization()
        .set_image_blob_channel_axis(-1, 0)
        .set_image_blob_shape((222, 222), 0)
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

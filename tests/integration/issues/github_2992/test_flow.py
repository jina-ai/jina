from jina import Document, Flow
from jina.types.arrays.memmap import DocumentArrayMemmap


def test_dam_flow(tmpdir):
    def _assert_called_once(response):
        assert len(response.docs) == 1
        assert not _assert_called_once.called
        _assert_called_once.called = True

    _assert_called_once.called = False

    f = Flow().add()
    dam = DocumentArrayMemmap(tmpdir)
    dam.append(Document())
    with f:
        response = f.post('/', dam, on_always=_assert_called_once, return_results=True)
    assert len(response.docs) == 1

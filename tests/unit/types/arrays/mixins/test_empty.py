from jina import DocumentArray, DocumentArrayMemmap


def test_empty_non_zero():
    da = DocumentArray.empty(10)
    assert len(da) == 10
    dam = DocumentArrayMemmap.empty(10)
    assert len(dam) == 10


def test_empty_zero():
    da = DocumentArray.empty()
    assert len(da) == 0
    dam = DocumentArrayMemmap.empty()
    assert len(dam) == 0

from jina import Document, Flow
from jina.types.arrays.memmap import DocumentArrayMemmap


def test_dam_flow(tmpdir):
    f = Flow().add()
    dam = DocumentArrayMemmap(tmpdir)
    dam.append(Document())
    with f:
        response = f.post('/', dam, return_results=True)
    assert len(response) == 1
    assert len(response[0].docs) == 1

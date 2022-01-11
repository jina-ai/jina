from jina import Document, Flow, DocumentArrayMemmap, Client

exposed_port = 12345


def test_dam_flow(tmpdir):
    f = Flow(port_expose=exposed_port).add()
    dam = DocumentArrayMemmap(tmpdir)
    dam.append(Document())
    with f:
        response = Client(port=exposed_port).post('/', dam, return_results=True)
    assert len(response) == 1
    assert len(response[0].docs) == 1

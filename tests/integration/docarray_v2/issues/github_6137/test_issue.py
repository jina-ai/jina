from docarray import DocList, BaseDoc
from docarray.documents.text import TextDoc
from jina import Executor, requests, Flow


def test_issue():
    class QuoteFile(BaseDoc):
        quote_file_id: int = None
        texts: DocList[TextDoc] = None

    class SearchResult(BaseDoc):
        results: DocList[QuoteFile] = None

    class InitialExecutor(Executor):

        @requests(on='/search')
        async def search(self, docs: DocList[SearchResult], **kwargs) -> DocList[SearchResult]:
            return docs

    f = (
        Flow(protocol='http')
            .add(name='initial', uses=InitialExecutor)
    )

    with f:
        resp = f.post(on='/search', inputs=DocList[SearchResult]([SearchResult(results=DocList[QuoteFile](
            [QuoteFile(quote_file_id=999, texts=DocList[TextDoc]([TextDoc(text='hey here')]))]))]),
                      return_type=DocList[SearchResult])
        assert resp[0].results[0].quote_file_id == 999
        assert resp[0].results[0].texts[0].text == 'hey here'

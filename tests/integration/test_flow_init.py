from jina import executable, Flow
from docarray import Document, DocumentArray


def test_executor_decorator():
    @executable
    def my_awesome_function(docs, **kwargs):
        for doc in docs:
            doc.text = "wow"

    def assert_result(resp):
        for doc in resp.docs:
            assert doc.text == "wow"

    f = Flow().add(uses=my_awesome_function)

    with f:
        f.search(DocumentArray([Document(text="")]), on_done=assert_result)

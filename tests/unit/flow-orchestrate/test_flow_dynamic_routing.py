from jina import Document, Executor, Flow, requests


class SimplExecutor(Executor):
    @requests
    def add_text(self, docs, **kwargs):
        docs[0].text = 'Hello World!'


def test_simple_routing():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(on='/index', inputs=[Document()], return_results=True)
        assert results[0].docs[0].text == 'Hello World!'


class MergeExecutor(Executor):
    @requests
    def add_text(self, docs, docs_matrix, **kwargs):
        if {docs[0].text, docs[1].text} == {'Hello World!', '1'}:
            docs[0].text = str(len(docs_matrix))


def test_expected_messages_routing():
    f = (
        Flow()
        .add(name='foo', uses=SimplExecutor)
        .add(name='bar', uses=MergeExecutor, needs=['foo', 'gateway'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
        assert results[0].docs[0].text == '2'


class SimplAddExecutor(Executor):
    @requests
    def add_doc(self, docs, **kwargs):
        docs.append(Document(text=self.runtime_args.name))


def test_shards():
    f = Flow().add(uses=SimplAddExecutor, shards=2)

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
        assert len(results[0].docs) == 2


class MergeDocsExecutor(Executor):
    @requests
    def add_doc(self, docs, **kwargs):
        return docs


def test_complex_flow():
    f = (
        Flow()
        .add(name='first', uses=SimplAddExecutor, needs=['gateway'])
        .add(name='forth', uses=SimplAddExecutor, needs=['first'], shards=2)
        .add(
            name='second_shards_needs',
            uses=SimplAddExecutor,
            needs=['gateway'],
            shards=2,
        )
        .add(
            name='third',
            uses=SimplAddExecutor,
            shards=3,
            needs=['second_shards_needs'],
        )
        .add(name='merger', uses=MergeDocsExecutor, needs=['forth', 'third'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
    assert len(results[0].docs) == 6
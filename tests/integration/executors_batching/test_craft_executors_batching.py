from jina.executors.crafters import BaseCrafter
from jina.executors.decorators import batching, batching_multi_input
from jina import Document
from jina.types.sets import DocumentSet


class DummyCrafterText(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3)
    def craft(self, text, *args, **kwargs):
        assert len(text) == 3
        return [{'text': f'{txt}-crafted'} for txt in text]


def test_batching_text_single():
    docs = DocumentSet([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs._extract_docs('text')

    crafter = DummyCrafterText()
    crafted_docs = crafter.craft(texts)
    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'


class DummyCrafterTextId(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching_multi_input(batch_size=3, num_data=2)
    def craft(self, text, id, *args, **kwargs):
        assert len(text) == 3
        assert len(id) == 3
        return [{'text': f'{txt}-crafted', 'id': f'{i}-crafted'} for i, txt in zip(id, text)]


def test_batching_text_multi():
    docs = DocumentSet([Document(text=f'text-{i}', id=f'id-{i}') for i in range(15)])
    required_keys = ['text', 'id']
    text_ids, _ = docs._extract_docs(*required_keys)

    crafter = DummyCrafterTextId()
    args = [text_ids[:, i] for i in range(len(required_keys))]
    crafted_docs = crafter.craft(*args)

    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'
        assert crafted_doc['id'] == f'id-{i}-crafted'

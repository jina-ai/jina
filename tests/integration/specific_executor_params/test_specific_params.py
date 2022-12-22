import numpy as np
from docarray import Document, DocumentArray, dataclass
from docarray.typing import Text

from jina import Executor, Flow, requests


def test_specific_params():
    class MyExec(Executor):
        def __init__(self, params_awaited, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.params_awaited = params_awaited

        @requests
        def process(self, docs, parameters, **kwargs):
            for doc in docs:
                doc.tags['assert'] = parameters == self.params_awaited

    flow = (
        Flow()
        .add(uses=MyExec, name='exec1', uses_with={'params_awaited': {'key_1': True}})
        .add(
            uses=MyExec,
            name='exec2',
            uses_with={'params_awaited': {'key_1': True, 'key_2': False}},
        )
    )

    with flow:
        docs = flow.index(
            DocumentArray.empty(size=1),
            parameters={'key_1': True, 'exec2__key_2': False},
        )

        assert docs[0].tags['assert']


def test_specific_params_with_branched_flow():
    class TextEncoderTestSpecific(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model = lambda t: np.random.rand(
                len(t), 128
            )  # initialize dummy text embedding model

        @requests(on='/encode')
        def encode_text(self, docs, parameters, **kwargs):
            path = parameters.get('access_path', None)
            text_docs = docs[path]
            embeddings = self.model(text_docs[:, 'text'])
            text_docs.embeddings = embeddings

    class EmbeddingCombinerTestSpecific(Executor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model = lambda emb1, emb2: np.concatenate(
                [emb1, emb2], axis=1
            )  # initialize dummy model to combine embeddings

        @requests(on='/encode')
        def combine(self, docs, parameters, **kwargs):
            text1_path = parameters.get('text1_access_path', None)
            text2_path = parameters.get('text2_access_path', None)
            assert text1_path == '@.[text1]'
            assert text2_path == '@.[text2]'
            text1_docs = docs[text1_path]
            text2_docs = docs[text2_path]
            combined_embeddings = self.model(
                text1_docs.embeddings, text2_docs.embeddings
            )
            docs.embeddings = combined_embeddings

    @dataclass
    class MMDoc:
        text1: Text
        text2: Text

    mmdoc_dataclass = MMDoc(text1='text 1', text2='text 2')
    da = DocumentArray([Document(mmdoc_dataclass)])
    f = (
        Flow()
        .add(uses=TextEncoderTestSpecific, name='Text1Encoder')
        .add(uses=TextEncoderTestSpecific, name='Text2Encoder', needs='gateway')
        .add(
            uses=EmbeddingCombinerTestSpecific,
            name='Combiner',
            needs=['Text1Encoder', 'Text2Encoder'],
        )
    )

    with f:
        da = f.post(
            inputs=da,
            on='/encode',
            parameters={
                'Text1Encoder__access_path': '@.[text1]',
                'Text2Encoder__access_path': '@.[text2]',
                'Combiner__text1_access_path': '@.[text1]',
                'Combiner__text2_access_path': '@.[text2]',
            },
        )

    assert len(da) == 1
    for d in da:
        assert d.embedding.shape == (256,)

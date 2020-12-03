from jina.types.sets import DocumentSet
from jina.types.sets.document_set import MultimodalDocumentSet
from jina.types.document.multimodal import MultimodalDocument


def test_from_documents_set():
    docs = []
    for i in range(0, 3):
        doc = MultimodalDocument.from_modality_content_mapping({'modA': f'textA {i}', 'modB': f'textB {i}'})
        docs.append(doc)

    for doc in MultimodalDocumentSet(docs):
        assert len(doc.chunks) == 2

    for doc in MultimodalDocumentSet(DocumentSet(docs)):
        assert len(doc.chunks) == 2

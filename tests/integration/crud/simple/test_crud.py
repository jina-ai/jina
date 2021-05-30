import numpy as np
from jina import Flow
from tests import random_docs

# noinspection PyUnresolvedReferences
from tests.integration.crud import CrudIndexer


def test_crud(tmpdir):
    with Flow.load_config('flow.yml') as f:
        original_docs = list(random_docs(10, chunks_per_doc=0))
        f.post(
            on='/index',
            inputs=original_docs,
        )
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 10

        f.post(on='/delete', inputs=random_docs(5, chunks_per_doc=0))
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 5

        updated_docs = list(
            random_docs(5, chunks_per_doc=0, start_id=5, text=b'hello again')
        )
        f.post(on='/update', inputs=updated_docs)
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 5
        matches = results[0].docs[0].matches
        matches = sorted(matches, key=lambda match: match.id)
        for match, updated_doc in zip(matches, updated_docs):
            assert updated_doc.id == match.id
            assert updated_doc.text == match.text
            np.testing.assert_array_equal(updated_doc.embedding, match.embedding)

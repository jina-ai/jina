import numpy as np
import os

from jina import Flow
from tests import random_docs

# noinspection PyUnresolvedReferences
from tests.integration.crud import CrudIndexer


def test_crud(tmpdir):
    os.environ['WORKSPACE'] = str(tmpdir)
    with Flow.load_config('flow.yml') as f:
        original_docs = list(random_docs(10, chunks_per_doc=0))
        f.post(
            on='/index',
            inputs=original_docs,
        )

    with Flow.load_config('flow.yml') as f:
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 10

    with Flow.load_config('flow.yml') as f:
        f.post(on='/delete', inputs=random_docs(5, chunks_per_doc=0))

    with Flow.load_config('flow.yml') as f:
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 5

    updated_docs = list(
        random_docs(5, chunks_per_doc=5, start_id=5, text=b'hello again')
    )

    with Flow.load_config('flow.yml') as f:
        f.post(on='/update', inputs=updated_docs)

    with Flow.load_config('flow.yml') as f:
        results = f.post(on='/search', inputs=random_docs(1), parameters={'top_k': 10})
        assert len(results[0].docs[0].matches) == 5
        matches = results[0].docs[0].matches
        matches = sorted(matches, key=lambda match: match.id)
        for match, updated_doc in zip(matches, updated_docs):
            assert updated_doc.id == match.id
            assert updated_doc.text == match.text
            np.testing.assert_array_equal(updated_doc.embedding, match.embedding)
            assert len(match.chunks) == 5
            assert len(match.chunks) == len(updated_doc.chunks)
            for match_chunk, updated_doc_chunk in zip(match.chunks, updated_doc.chunks):
                assert match_chunk.text == updated_doc_chunk.text
                np.testing.assert_array_equal(
                    match_chunk.embedding, updated_doc_chunk.embedding
                )

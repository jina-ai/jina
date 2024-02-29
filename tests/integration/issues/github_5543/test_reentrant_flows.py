import pytest
from jina import Flow, DocumentArray


@pytest.mark.parametrize('use_stream', [False, True])
def test_reentrant(use_stream):
    for _ in range(10):
        f = Flow().add()
        with f:
            docs = f.post(
                on='/',
                inputs=DocumentArray.empty(100),
                request_size=1,
                stream=use_stream,
            )
            assert len(docs) == 100

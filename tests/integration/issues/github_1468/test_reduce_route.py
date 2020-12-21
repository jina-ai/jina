import pytest

from jina.flow import Flow
from jina.types.document.multimodal import MultimodalDocument


def multimodal_generator():
    for i in range(0, 5):
        document = MultimodalDocument(modality_content_map={'1': f'aaa {i}', '2': f'bbb {i}'})
        yield document


@pytest.mark.skip(' Failing until issue 1468 is fixed ')
@pytest.mark.timeout(10)
def test_reduce_route():
    with Flow.load_config('flow.yml') as f:
        f.search(input_fn=multimodal_generator())

import numpy as np
import pytest
import torch

from docarray import Document, DocumentArray


@pytest.mark.parametrize(
    'array', [(1, 2, 3), [1, 2, 3], np.array([1, 2, 3]), torch.tensor([1, 2, 3])]
)
@pytest.mark.parametrize('attr', ['embedding', 'blob'])
def test_single_doc_dict_json(attr, array):
    d = Document({attr: array})
    assert d.dict()[attr] == list(array)
    j = d.json()
    assert '1,' in j and '2,' in j and '3' in j

    assert getattr(Document(j), attr).tolist() == [1, 2, 3]


def test_docarray_list():
    da = DocumentArray.empty(10)
    da.embeddings = np.random.random([10, 3])
    da.blobs = np.random.random([10, 24, 24, 3])
    dal = da.to_list()
    assert len(dal) == 10
    assert isinstance(dal[0]['embedding'], list)
    da2 = DocumentArray.load_json(da.to_json())
    assert len(da2) == 10
    assert da2.embeddings.shape == (10, 3)
    assert da2.blobs.shape == (10, 24, 24, 3)

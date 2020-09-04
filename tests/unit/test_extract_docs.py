import numpy as np

from jina.drivers.helper import extract_docs, array2pb
from jina.proto import jina_pb2


def test_extract_docs():
    d = jina_pb2.Document()

    contents, docs_pts, bad_doc_ids = extract_docs([d], embedding=True)
    assert len(bad_doc_ids) > 0
    assert contents is None

    vec = np.random.random([2, 2])
    d.embedding.CopyFrom(array2pb(vec))
    contents, docs_pts, bad_doc_ids = extract_docs([d], embedding=True)
    assert len(bad_doc_ids) == 0
    np.testing.assert_equal(contents[0], vec)

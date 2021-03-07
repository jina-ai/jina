import numpy as np

from jina import Flow, Document

from tests import validate_callback


def test_crud_in_readme(mocker):
    docs = [
        Document(
            id='🐲',
            embedding=np.array([0, 0]),
            tags={'guardian': 'Azure Dragon', 'position': 'East'},
        ),
        Document(
            id='🐦',
            embedding=np.array([1, 0]),
            tags={'guardian': 'Vermilion Bird', 'position': 'South'},
        ),
        Document(
            id='🐢',
            embedding=np.array([0, 1]),
            tags={'guardian': 'Black Tortoise', 'position': 'North'},
        ),
        Document(
            id='🐯',
            embedding=np.array([1, 1]),
            tags={'guardian': 'White Tiger', 'position': 'West'},
        ),
    ]

    # create
    mock = mocker.Mock()
    with Flow().add(uses='_index') as f:
        f.index(docs, on_done=mock)

    mock.assert_called_once()

    # read
    def validate(req):
        assert len(req.docs[0].matches) == 3
        for match in req.docs[0].matches:
            assert match.id != '🐯'
            assert 'position' in match.tags
            assert 'guardian' in match.tags
            assert match.score.ref_id == req.docs[0].id

    mock = mocker.Mock()

    with f:
        f.search(docs[0], top_k=3, on_done=mock)
    validate_callback(mock, validate)

    # update
    mock = mocker.Mock()

    d = docs[0]
    d.embedding = np.array([1, 1])
    with f:
        f.update(d, on_done=mock)
    mock.assert_called_once()

    # search again

    def validate(req):
        assert len(req.docs[0].matches) == 1
        req.docs[0].matches[0].id = req.docs[0].id
        # embeddings are removed in the CompoundIndexer via ExcludeQL
        np.testing.assert_array_equal(req.docs[0].matches[0].embedding, np.array(None))

    mock = mocker.Mock()

    with f:
        f.search(docs[0], top_k=1, on_done=mock)
    validate_callback(mock, validate)

    # delete
    mock = mocker.Mock()

    with f:
        f.delete(['🐦', '🐲'], on_done=mock)
    mock.assert_called_once()

    # search again

    def validate(req):
        assert len(req.docs[0].matches) == 2

    mock = mocker.Mock()

    with f:
        f.search(docs[0], top_k=4, on_done=mock)
    validate_callback(mock, validate)

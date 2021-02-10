import numpy as np

from jina import Flow, Document


def test_crud_in_readme(mocker):
    docs = [Document(id='🐲', embedding=np.array([0, 0]), tags={'guardian': 'Azure Dragon', 'position': 'East'}),
            Document(id='🐦', embedding=np.array([1, 0]), tags={'guardian': 'Vermilion Bird', 'position': 'South'}),
            Document(id='🐢', embedding=np.array([0, 1]), tags={'guardian': 'Black Tortoise', 'position': 'North'}),
            Document(id='🐯', embedding=np.array([1, 1]), tags={'guardian': 'White Tiger', 'position': 'West'})]

    # create
    m = mocker.Mock()
    with Flow().add(uses='_index') as f:
        f.index(docs, on_done=m)

    m.assert_called_once()

    # read
    def validate(req):
        assert len(req.docs[0].matches) == 3
        for m in req.docs[0].matches:
            assert m.id != '🐯'
            assert 'position' in m.tags
            assert 'guardian' in m.tags
            # when is_update set to False, m.score is empty
            assert m.score.value
            assert m.score.ref_id == req.docs[0].id

    m = mocker.Mock(wrap=validate)

    with f:
        f.search(docs[0],
                 top_k=3,
                 on_done=m)
    m.assert_called_once()

    # update
    m = mocker.Mock()

    d = docs[0]
    d.embedding = np.array([1, 1])
    with f:
        f.update(d, on_done=m)
    m.assert_called_once()

    # search again

    def validate(req):
        assert len(req.docs[0].matches) == 1
        req.docs[0].matches[0].id = req.docs[0].id
        np.testing.assert_array_equal(req.docs[0].matches[0].embedding, docs[0].embedding)

    m = mocker.Mock(wrap=validate)

    with f:
        f.search(docs[0],
                 top_k=1,
                 on_done=m)
    m.assert_called_once()

    # delete
    m = mocker.Mock()

    with f:
        f.delete(['🐦', '🐲'], on_done=m)
    m.assert_called_once()

    # search again

    def validate(req):
        assert len(req.docs[0].matches) == 2

    m = mocker.Mock(wrap=validate)

    with f:
        f.search(docs[0],
                 top_k=4,
                 on_done=m)
    m.assert_called_once()

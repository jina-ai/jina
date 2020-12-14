from jina.flow import Flow

f = Flow().add()

def test_bad_iterator():
    # This will get stuck as iterator is bad
    # This is the reason, we had added a timeout to request_iterator in the servicer
    with f:
        f.index([1, 2, 3])



class DummySparseEncoder(BaseEncoder):
    def encode(self, data, *args, **kwargs):
        # return sparse embedding with same number of rows as `data`.


class DummyCSRSparseIndexer(BaseIndexer):

    def add(self):
        #

    def query(self):
       #




def test_sparse_pipeline():

    f = Flow.add(uses=DummySparseEncoder).add(uses=DummyCSRSparseIndexer)

    with f:
        f.index(inputs=[], on_done=)
        f.search(inputs=[], on_done=validate)
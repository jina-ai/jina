from jina import Executor, requests


class Override(Executor):
    def __init__(self, param1, param2, param3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3

    @requests(on='/search')
    def encode(self, docs, **kwargs):
        for doc in docs:
            doc.tags['param1'] = self.param1
            doc.tags['param2'] = self.param2
            doc.tags['param3'] = self.param3
            doc.tags['workspace'] = getattr(self.metas, 'workspace')
            doc.tags['name'] = getattr(self.metas, 'name')

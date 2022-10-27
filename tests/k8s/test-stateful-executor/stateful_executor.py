import os
from jina import Executor, requests, DocumentArray


class StatefulExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store_path = os.path.join(self.workspace, 'docarray.bin')
        if os.path.exists(self.store_path):
            self._da = DocumentArray.load_binary(self.store_path)
        else:
            self._da = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._da.extend(docs)

    @requests(on='/len')
    def length(self, **kwargs):
        return {'length': len(self._da)}

    def close(self) -> None:
        self._da.save_binary(self.store_path)
        super().close()

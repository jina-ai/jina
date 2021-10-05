from pathlib import Path

import requests as py_req
from jina import Executor, requests, DocumentArray


class CacheValidator(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exists = False
        self.cache_path = Path.home() / '.company' / 'model.blah'
        if not self.cache_path.exists():
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            response = py_req.get('https://jina.ai')
            with open(self.cache_path, 'w') as f:
                f.write(response.text)
        else:
            self.exists = True

    @requests
    def foo(self, docs: DocumentArray, *args, **kwargs):
        docs[0].tags['exists'] = self.exists

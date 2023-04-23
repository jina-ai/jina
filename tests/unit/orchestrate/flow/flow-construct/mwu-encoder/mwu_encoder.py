import os

from typing import Any

from jina import Executor, requests


class MWUEncoder(Executor):
    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    @requests
    def encode(self, docs, **kwargs) -> Any:
        for doc in docs:
            doc.tags['greetings'] = self._greetings

    def close(self) -> None:
        import pickle

        os.makedirs(self.workspace, exist_ok=True)
        bin_path = os.path.join(self.workspace, f'{self.metas.name}.bin')
        with open(bin_path, 'wb', encoding='utf-8') as f:
            pickle.dump(self._greetings, f)

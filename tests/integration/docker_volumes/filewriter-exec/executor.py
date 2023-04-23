import os

from jina import Executor, requests


class FilewriterExec(Executor):
    @requests
    def foo(self, **kwargs):
        print(self.workspace)
        file = os.path.join(self.workspace, 'out.txt')
        with open(file, 'w', encoding='utf-8') as f:
            f.write('Filewriter was here')

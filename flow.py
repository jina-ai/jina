import random

from docarray import DocumentArray

from jina import Executor, Flow, requests


class MyExecutor(Executor):
    @requests
    def boo(self, docs: DocumentArray, **kwargs):
        print('MyExecutor called')
        for doc in docs:
            doc.text = f'my doc{random.randint(1, 100)}'


flow = (
    Flow()
    .config_gateway(port=8501, protocol='http', uses='streamlit_gateway/config.yml')
    .add(uses=MyExecutor)
)
with flow:
    flow.block()

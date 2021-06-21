from jina import Executor, requests, DocumentArray
from jina.logging.logger import JinaLogger


class DummyTextEvaluator(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger(self.__class__.__name__)

    @requests
    def evaluate(self, docs: 'DocumentArray', groundtruths: 'DocumentArray', **kwargs):
        for doc, groundtruth in zip(docs, groundtruths):
            doc.evaluations['DummyScore'] = 1.0 if doc.text == groundtruth.text else 0.0
            doc.evaluations['DummyScore'].op_name = f'DummyScore'

from jina import Executor, requests, DocumentArray
from jina.logging.logger import JinaLogger


class DummyTextEvaluator(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger(self.__class__.__name__)

    @requests
    def evaluate(self, docs: 'DocumentArray', groundtruths: 'DocumentArray', **kwargs):
        for doc, groundtruth in zip(docs, groundtruths):
            evalulation = doc.evaluations.add()
            evalulation.op_name = f'DummyScore'
            if doc.text == groundtruth.text:
                evalulation.value = 1.0
            else:
                evalulation.value = 0.0

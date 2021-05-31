from jina import Executor, requests, DocumentArray


class DummyTextEvaluator(Executor):
    @property
    def metric(self) -> str:
        return 'DummyTextEvaluator'

    @requests
    def evaluate(self, docs: 'DocumentArray', groundtruths: 'DocumentArray', **kwargs):
        for doc, groundtruth in zip(docs, groundtruths):
            evalulation = doc.evaluations.add()
            evalulation.op_name = f'DummyScore'
            if doc.text == groundtruth.text:
                evalulation.value = 1.0
            else:
                evalulation.value = 0.0

from jina.executors.evaluators.text import BaseTextEvaluator


class DummyTextEvaluator(BaseTextEvaluator):
    @property
    def metric(self) -> str:
        return 'DummyTextEvaluator'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def evaluate(self, actual: str, desired: str, *args, **kwargs) -> float:
        if actual == desired:
            return 1.0
        else:
            return 0.0

from jina import Executor, requests

from jina.optimizers.parameters import IntegerParameter


class DummyCrafter(Executor):
    DEFAULT_OPTIMIZATION_PARAMETER = [
        IntegerParameter(
            executor_name='DummyCrafter',
            parameter_name='param1',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafter',
            parameter_name='param2',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafter',
            parameter_name='param3',
            low=0,
            high=2,
            step_size=1,
        ),
    ]

    GOOD_PARAM_1 = 0
    GOOD_PARAM_2 = 1
    GOOD_PARAM_3 = 1

    def __init__(self, param1: int, param2: int, param3: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3

    @property
    def good_params(self):
        return (
            self.param1 == DummyCrafter.GOOD_PARAM_1
            and self.param2 == DummyCrafter.GOOD_PARAM_2
            and self.param3 == DummyCrafter.GOOD_PARAM_3
        )

    @requests
    def craft(self, docs, *args, **kwargs):
        for doc in docs:
            if not self.good_params:
                doc.text = ''

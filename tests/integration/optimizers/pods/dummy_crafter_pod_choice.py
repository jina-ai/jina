from jina import Executor, requests

from jina.optimizers.parameters import IntegerParameter
from jina.logging.logger import JinaLogger


class DummyCrafterOption1(Executor):
    DEFAULT_OPTIMIZATION_PARAMETER = [
        IntegerParameter(
            executor_name='DummyCrafterOption1',
            parameter_name='param1',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafterOption1',
            parameter_name='param2',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafterOption1',
            parameter_name='param3',
            low=0,
            high=1,
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
        self.logger = JinaLogger(self.__class__.__name__)

    @property
    def good_params(self):
        return (
            self.param1 == DummyCrafterOption1.GOOD_PARAM_1
            and self.param2 == DummyCrafterOption1.GOOD_PARAM_2
            and self.param3 == DummyCrafterOption1.GOOD_PARAM_3
        )

    @requests
    def craft(self, docs, *args, **kwargs):
        for doc in docs:
            if not self.good_params:
                doc.text = ''
            if self.good_params and doc.text == 'DummyCrafterOption1':
                doc.text = 'hello'


class DummyCrafterOption2(Executor):
    DEFAULT_OPTIMIZATION_PARAMETER = [
        IntegerParameter(
            executor_name='DummyCrafterOption2',
            parameter_name='param4',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafterOption2',
            parameter_name='param5',
            low=0,
            high=1,
            step_size=1,
        ),
        IntegerParameter(
            executor_name='DummyCrafterOption2',
            parameter_name='param6',
            low=0,
            high=1,
            step_size=1,
        ),
    ]

    GOOD_PARAM_4 = 0
    GOOD_PARAM_5 = 1
    GOOD_PARAM_6 = 1

    def __init__(self, param4: int, param5: int, param6: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param4 = param4
        self.param5 = param5
        self.param6 = param6
        self.logger = JinaLogger(self.__class__.__name__)

    @property
    def good_params(self):
        return (
            self.param4 == DummyCrafterOption2.GOOD_PARAM_4
            and self.param5 == DummyCrafterOption2.GOOD_PARAM_5
            and self.param6 == DummyCrafterOption2.GOOD_PARAM_6
        )

    @requests
    def craft(self, docs, *args, **kwargs):
        for doc in docs:
            if not self.good_params:
                doc.text = ''
            if self.good_params and doc.text == 'DummyCrafterOption2':
                doc.text = 'hello'

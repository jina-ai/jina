from typing import Optional, Sequence, Union

from ..jaml import JAML, JAMLCompatible


class OptimizationParameter(JAMLCompatible):
    def __init__(
        self,
        parameter_name: str = "",
        executor_name: Optional[str] = None,
        prefix: str = 'JINA',
        jaml_variable: Optional[str] = None,
    ):
        self.parameter_name = parameter_name
        if jaml_variable is None:
            self.jaml_variable = f'{prefix}_{executor_name}_{parameter_name}'.upper()
        else:
            self.jaml_variable = jaml_variable


class IntegerParameter(OptimizationParameter):
    def __init__(
        self,
        low: int,
        high: int,
        step_size: int = 1,
        log: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.step_size = step_size
        # The step != 1 and log arguments cannot be used at the same time.
        # To set the log argument to True, set the step argument to 1.
        self.log = log


class FloatParameter(OptimizationParameter):
    def __init__(
        self,
        low: float,
        high: float,
        step_size: Optional[float] = None,
        log: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.step_size = step_size
        self.log = log


class UniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high


class LogUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high


class CategoricalParameter(OptimizationParameter):
    def __init__(
        self, choices: Sequence[Union[None, bool, int, float, str]], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.choices = choices


class DiscreteUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, q: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.q = q


def load_optimization_parameters(filepath: str):

    with open(filepath, encoding='utf8') as fp:
        return JAML.load(fp)

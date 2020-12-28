from typing import Optional, Sequence, Union

import inspect

from ..jaml import JAML


class OptimizationParameter:
    def __init__(
        self,
        parameter_name: str,
        executor_name: Optional[str] = None,
        prefix: str = 'JINA',
        env_var: Optional[str] = None,
    ):
        if env_var is None:
            self.env_var = f'{prefix}_{executor_name}_{parameter_name}'.upper()
        else:
            self.env_var = env_var
        self.parameter_name = parameter_name

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`pyyaml` """
        tmp = data._dump_instance_to_yaml(data)
        representer.sort_base_mapping_type_on_output = False
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @staticmethod
    def _dump_instance_to_yaml(instance):

        attributes = inspect.getmembers(instance, lambda a: not (inspect.isroutine(a)))
        return {
            a[0]: a[1]
            for a in attributes
            if not (a[0].startswith('__') and a[0].endswith('__'))
        }

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`pyyaml` """
        return cls._get_instance_from_yaml(constructor, node)

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):
        data = constructor.construct_mapping(node, deep=True)
        return cls(**data)


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
        self.optuna_method = 'suggest_int'

    def to_optuna_args(self):
        return {
            'name': self.env_var,
            'low': self.low,
            'high': self.high,
            'step': self.step_size,
            'log': self.log,
        }


JAML.register(IntegerParameter)


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
        self.optuna_method = 'suggest_float'

    def to_optuna_args(self):
        return {
            'name': self.env_var,
            'low': self.low,
            'high': self.high,
            'step': self.step_size,
            'log': self.log,
        }


JAML.register(FloatParameter)


class UniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.optuna_method = 'suggest_uniform'

    def to_optuna_args(self):
        return {
            'name': self.env_var,
            'low': self.low,
            'high': self.high,
        }


JAML.register(UniformParameter)


class LogUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.optuna_method = 'suggest_loguniform'

    def to_optuna_args(self):
        return {
            'name': self.env_var,
            'low': self.low,
            'high': self.high,
        }


JAML.register(LogUniformParameter)


class CategoricalParameter(OptimizationParameter):
    def __init__(
        self, choices: Sequence[Union[None, bool, int, float, str]], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.choices = choices
        self.optuna_method = 'suggest_categorical'

    def to_optuna_args(self):
        return {'name': self.env_var, 'choices': self.choices}


JAML.register(CategoricalParameter)


class DiscreteUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, q: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.q = q
        self.optuna_method = 'suggest_discrete_uniform'

    def to_optuna_args(self):
        return {
            'name': self.env_var,
            'low': self.low,
            'high': self.high,
            'q': self.q,
        }


JAML.register(DiscreteUniformParameter)


def load_optimization_parameters(filepath: str):
    JAML.register(IntegerParameter)
    JAML.register(FloatParameter)
    JAML.register(UniformParameter)
    JAML.register(LogUniformParameter)
    JAML.register(CategoricalParameter)
    JAML.register(DiscreteUniformParameter)
    with open(filepath, encoding='utf8') as fp:
        return JAML.load(fp)

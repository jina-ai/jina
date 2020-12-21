from typing import Optional, Sequence, Union

import inspect
import ruamel.yaml

from jina.helper import yaml


class OptimizationParameter:
    def __init__(
        self,
        parameter_name: str,
        executor_name: Optional[str] = None,
        prefix: str = "JINA",
        env_var: Optional[str] = None,
        method:Optional[str] = None
    ):
        if env_var is None:
            self.env_var = f"{prefix}_{executor_name}_{parameter_name}".upper()
        else:
            self.env_var = env_var
        self.parameter_name = parameter_name

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        representer.sort_base_mapping_type_on_output = False
        return representer.represent_mapping("!" + cls.__name__, tmp)

    @staticmethod
    def _dump_instance_to_yaml(instance):

        attributes = inspect.getmembers(instance, lambda a: not (inspect.isroutine(a)))
        return {
            a[0]: a[1]
            for a in attributes
            if not (a[0].startswith("__") and a[0].endswith("__"))
        }

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node)

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):
        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True
        )
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
        self.log = log
        self.method = "suggest_int"

    def to_optuna_args(self):
        return {
            "name": self.env_var,
            "low": self.low,
            "high": self.high,
            "step": self.step_size,
            "log": self.log,
        }

yaml.register_class(IntegerParameter)

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
        self.method = "suggest_float"

    def to_optuna_args(self):
        return {
            "name": self.env_var,
            "low": self.low,
            "high": self.high,
            "step": self.step_size,
            "log": self.log,
        }

yaml.register_class(FloatParameter)

class UniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.method = "suggest_uniform"

    def to_optuna_args(self):
        return {
            "name": self.env_var,
            "low": self.low,
            "high": self.high,
        }

yaml.register_class(UniformParameter)

class LogUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.method = "suggest_loguniform"

    def to_optuna_args(self):
        return {
            "name": self.env_var,
            "low": self.low,
            "high": self.high,
        }

yaml.register_class(LogUniformParameter)

class CategoricalParameter(OptimizationParameter):
    def __init__(
        self, choices: Sequence[Union[None, bool, int, float, str]], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.choices = choices
        self.method = "suggest_categorical"

    def to_optuna_args(self):
        return {"name": self.env_var, "choices": self.choices}

yaml.register_class(CategoricalParameter)

class DiscreteUniformParameter(OptimizationParameter):
    def __init__(self, low: float, high: float, q: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.q = q
        self.method = "suggest_discrete_uniform"

    def to_optuna_args(self):
        return {
            "name": self.env_var,
            "low": self.low,
            "high": self.high,
            "q": self.q,
        }

yaml.register_class(DiscreteUniformParameter)

def load_optimization_parameters(filename):
    yaml.register_class(IntegerParameter)
    yaml.register_class(FloatParameter)
    yaml.register_class(UniformParameter)
    yaml.register_class(LogUniformParameter)
    yaml.register_class(CategoricalParameter)
    yaml.register_class(DiscreteUniformParameter)
    with open(filename, encoding="utf8") as fp:
        return yaml.load(fp)
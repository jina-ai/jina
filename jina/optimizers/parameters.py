from abc import abstractmethod
from typing import Optional, Sequence, Union

from ..jaml import JAML, JAMLCompatible

if False:
    from optuna.trial import Trial


class OptimizationParameter(JAMLCompatible):
    """Base class for all optimization parameters."""

    def __init__(
        self,
        parameter_name: str = '',
        executor_name: Optional[str] = None,
        prefix: str = 'JINA',
        jaml_variable: Optional[str] = None,
    ):
        self.parameter_name = parameter_name
        if jaml_variable is None:
            self.jaml_variable = f'{prefix}_{executor_name}_{parameter_name}'.upper()
        else:
            self.jaml_variable = jaml_variable

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        raise NotImplementedError


class IntegerParameter(OptimizationParameter):
    """
    Used for optimizing integer parameters with the FlowOptimizer.
    For detailed information about sampling and usage see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_int
    """

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
        if log and step_size != 1:
            raise ValueError(
                '''The step_size != 1 and log arguments cannot be used at the same time. When setting log argument to 
                True, set the step argument to 1. '''
            )

        self.step_size = step_size
        self.log = log

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_int(
            name=self.jaml_variable,
            low=self.low,
            high=self.high,
            step=self.step_size,
            log=self.log,
        )


class UniformParameter(OptimizationParameter):
    """
    Used for optimizing float parameters with the FlowOptimizer with uniform sampling.
    For detailed information about sampling and usage see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_discrete_uniform
    """

    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_uniform(
            name=self.jaml_variable,
            low=self.low,
            high=self.high,
        )


class LogUniformParameter(OptimizationParameter):
    """
    Used for optimizing float parameters with the FlowOptimizer with loguniform sampling.
    For detailed information about sampling and usage see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_loguniform
    """

    def __init__(self, low: float, high: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_loguniform(
            name=self.jaml_variable,
            low=self.low,
            high=self.high,
        )


class CategoricalParameter(OptimizationParameter):
    """
    Used for optimizing categorical parameters with the FlowOptimizer.
    For detailed information about sampling and usage see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_categorical
    """

    def __init__(
        self, choices: Sequence[Union[None, bool, int, float, str]], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_categorical(name=self.jaml_variable, choices=self.choices)


class DiscreteUniformParameter(OptimizationParameter):
    """
    Used for optimizing discrete parameters with the FlowOptimizer with uniform sampling.
    For detailed information about sampling and usage it is used by Jina with optuna see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_discrete_uniform
    """

    def __init__(self, low: float, high: float, q: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.q = q

    def suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_discrete_uniform(
            name=self.jaml_variable,
            low=self.low,
            high=self.high,
            q=self.q,
        )


def load_optimization_parameters(filepath: str):
    """
    Loads optimization parameters from a `.yml` file and parses it with the JAML parser.
    :param filepath: Path to a file that contains optimization parameters.
    :return:: The loaded :class:`OptimizationParameter` objects.
    """

    with open(filepath, encoding='utf8') as fp:
        return JAML.load(fp)

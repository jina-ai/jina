from typing import Any, Optional, Sequence, List, Dict, Union, TYPE_CHECKING

from ..jaml import JAML, JAMLCompatible

if TYPE_CHECKING:
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

    def _suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        raise NotImplementedError

    @property
    def search_space(self) -> Dict[str, List[Any]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :raises NotImplementedError: :class:`OptimizationParameter` is just an interface. Please
            use any implemented subclass.
        """
        raise NotImplementedError

    def update_trial_params(self, trial: 'Trial', trial_params: Dict):
        """
        Update the trial parameters given the variables and the trials

        :param trial: An instance of an Optuna Trial object
        :param trial_params: the parameters to update
            # noqa: DAR201
        """
        trial_params[self.jaml_variable] = self._suggest(trial)


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

    def _suggest(self, trial: 'Trial'):
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

    @property
    def search_space(self) -> Dict[str, List[int]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :return:: The parameter's search space in dictionary form with the parameter name as key
            and a list of values as value
        """
        return {
            self.jaml_variable: list(range(self.low, self.high + 1, self.step_size))
        }


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

    def _suggest(self, trial: 'Trial'):
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

    @property
    def search_space(self) -> Dict[str, List[Any]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :raises NotImplementedError: search space is not defined for parameter type
            :class:`UniformParameter`.
        """
        raise NotImplementedError(
            f"Can't define the search space of a {self.__class__.__name__}"
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

    def _suggest(self, trial: 'Trial'):
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

    @property
    def search_space(self) -> Dict[str, List[Any]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :raises NotImplementedError: search space is not defined for parameter type
            :class:`LogUniformParameter`.
        """
        raise NotImplementedError(
            f"Can't define the search space of a {self.__class__.__name__}"
        )


class CategoricalParameter(OptimizationParameter):
    """
    Used for optimizing categorical parameters with the FlowOptimizer.
    For detailed information about sampling and usage see
    https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.suggest_categorical
    """

    def __init__(
        self, choices: Sequence[Optional[Union[bool, int, float, str]]], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def _suggest(self, trial: 'Trial'):
        """
        Suggest an instance of the parameter for a given trial.

        :param trial: An instance of an Optuna Trial object
            # noqa: DAR201
        """
        return trial.suggest_categorical(name=self.jaml_variable, choices=self.choices)

    @property
    def search_space(self) -> Dict[str, List[Optional[Union[bool, int, float, str]]]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :return:: The parameter's search space in dictionary form with the parameter name as key
            and a list of values as value
        """
        return {self.jaml_variable: list(self.choices)}


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

    def _suggest(self, trial: 'Trial'):
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

    @property
    def search_space(self) -> Dict[str, List[float]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :return:: The parameter's search space in dictionary form with the parameter name as key
            and a list of values as value
        """
        search_space_values: List[float] = []
        value = self.low
        while value <= self.high:
            search_space_values.append(value)
            value += self.q

        return {self.jaml_variable: search_space_values}


class ExecutorAlternativeParameter(CategoricalParameter):
    """
    Used for optimizing alternative executor parameters.
    It selects from choices the same way as :class::CategoricalParameter does. Plus adds some inner parameters
    that expose different `OptimizationParameters` for each of the specific options.

        .. highlight:: python
        .. code-block:: python

            choices = ['executorA', 'executorB']
            inner_parameters = {
                    'executorA': [IntegerParameter(..., parameter_name='executorA_param1'),
                        CategoricalParameter(..., parameter_name='executorA_param2')],
                    'executorB': [IntegerParameter(..., parameter_name='executorB_param1'),
                        CategoricalParameter(..., parameter_name='executorB_param2')]
                    }

            parameter = ExecutorAlternativeParameter(choices=choices, inner_parameters=inner_parameters)
    """

    def __init__(
        self,
        inner_parameters: Dict[str, List[OptimizationParameter]],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        assert len(self.choices) == len(
            inner_parameters.keys()
        ), 'Every executor alternative needs to have its set of parameters'
        self.inner_parameters = inner_parameters

    @property
    def search_space(self) -> Dict[str, List[Any]]:
        """
        Get the parameter's search space, i.e. a dictionary mapping the parameter name to a list of
        possible values for the parameter.

        :return:: The parameter's search space in dictionary form with the parameter name as key
            and a list of values as value
        """
        search_space = super().search_space
        for _, inner_parameters in self.inner_parameters.items():
            for parameter in inner_parameters:
                search_space.update(parameter.search_space)

        return search_space

    def update_trial_params(self, trial: 'Trial', trial_params: Dict):
        """
        Update the trial parameters given the variables and the trials

        :param trial: An instance of an Optuna Trial object
        :param trial_params: the parameters to update
            # noqa: DAR201
        """
        super().update_trial_params(trial, trial_params)
        for param in self.inner_parameters[trial_params[self.jaml_variable]]:
            param.update_trial_params(trial, trial_params)


def load_optimization_parameters(filepath: str):
    """
    Loads optimization parameters from a `.yml` file and parses it with the JAML parser.
    :param filepath: Path to a file that contains optimization parameters.
    :return:: The loaded :class:`OptimizationParameter` objects.
    """

    with open(filepath, encoding='utf8') as fp:
        return JAML.load(fp)

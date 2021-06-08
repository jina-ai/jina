import pytest

import optuna

from jina.optimizers.parameters import (
    IntegerParameter,
    UniformParameter,
    LogUniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
)


@pytest.fixture()
def trials():
    from optuna.trial._state import TrialState

    ts = []
    for trial_id in range(10):
        ts.append(
            optuna.trial.create_trial(
                state=TrialState.RUNNING, params={'JINA_DUMMY': None}
            )
        )

    return ts


def test_integer_parameter(trials):
    parameter = IntegerParameter(
        jaml_variable='JINA_DUMMY',
        high=10,
        low=0,
        step_size=1,
        parameter_name='integer',
    )

    for trial in trials:
        trial_parameters = parameter.suggest(trial)
        print(f' trial_parameters {trial_parameters}')


def test_uniform_parameter(trials):
    parameter = UniformParameter(
        jaml_variable='JINA_DUMMY', high=10, low=0, parameter_name='uniform'
    )

    for trial in trials:
        trial_parameters = parameter.suggest(trial)
        print(f' trial_parameters {trial_parameters}')


def test_log_uniform_parameter(trials):
    parameter = LogUniformParameter(
        jaml_variable='JINA_DUMMY', high=10, low=0, parameter_name='loguniform'
    )

    for trial in trials:
        trial_parameters = parameter.suggest(trial)
        print(f' trial_parameters {trial_parameters}')


def test_categorical_parameter(trials):
    parameter = CategoricalParameter(
        jaml_variable='JINA_DUMMY',
        choices=[f'choice-{i}' for i in range(10)],
        parameter_name='categorical',
    )

    for trial in trials:
        trial_parameters = parameter.suggest(trial)
        print(f' trial_parameters {trial_parameters}')


def test_discrete_uniform_parameter(trials):
    parameter = DiscreteUniformParameter(
        jaml_variable='JINA_DUMMY',
        high=10,
        low=0,
        q=1,
        parameter_name='discreteuniform',
    )

    for trial in trials:
        trial_parameters = parameter.suggest(trial)
        print(f' trial_parameters {trial_parameters}')

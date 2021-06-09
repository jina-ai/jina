import pytest
import optuna

from jina.optimizers.parameters import (
    IntegerParameter,
    UniformParameter,
    LogUniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
    ExecutorAlternativeParameter,
)


@pytest.fixture()
def optuna_sampler():
    return optuna.samplers.TPESampler()


def test_integer_parameter(optuna_sampler):
    parameter = IntegerParameter(
        jaml_variable='JINA_DUMMY',
        high=10,
        low=0,
        step_size=1,
        parameter_name='integer',
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert 0 <= trial_parameters['JINA_DUMMY'] <= 10
        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)


def test_uniform_parameter(optuna_sampler):
    parameter = UniformParameter(
        jaml_variable='JINA_DUMMY', high=10, low=0, parameter_name='uniform'
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert 0 <= trial_parameters['JINA_DUMMY'] <= 10
        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)


def test_log_uniform_parameter(optuna_sampler):
    parameter = LogUniformParameter(
        jaml_variable='JINA_DUMMY', high=10, low=1, parameter_name='loguniform'
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert 0 <= trial_parameters['JINA_DUMMY'] <= 10
        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)


def test_categorical_parameter(optuna_sampler):
    parameter = CategoricalParameter(
        jaml_variable='JINA_DUMMY',
        choices=[f'choice-{i}' for i in range(10)],
        parameter_name='categorical',
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert trial_parameters['JINA_DUMMY'] in [f'choice-{i}' for i in range(10)]
        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)


def test_discrete_uniform_parameter(optuna_sampler):
    parameter = DiscreteUniformParameter(
        jaml_variable='JINA_DUMMY',
        high=10,
        low=0,
        q=1,
        parameter_name='discreteuniform',
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert 0 <= trial_parameters['JINA_DUMMY'] <= 10
        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)


def test_pod_alternative_parameter(optuna_sampler):
    inner_parameters = {
        'pod1': [
            IntegerParameter(
                jaml_variable='JINA_INTEGER_DUMMY_POD1',
                high=10,
                low=0,
                parameter_name='integerparam_pod1',
            ),
            CategoricalParameter(
                jaml_variable='JINA_CAT_DUMMY_POD1',
                choices=[f'choice-{i}' for i in range(10)],
                parameter_name='categorical_pod1',
            ),
        ],
        'pod2': [
            IntegerParameter(
                jaml_variable='JINA_INTEGER_DUMMY_POD2',
                high=10,
                low=0,
                parameter_name='integerparam_pod2',
            ),
            CategoricalParameter(
                jaml_variable='JINA_CAT_DUMMY_POD2',
                choices=[f'choice-{i}' for i in range(10)],
                parameter_name='categorical_pod2',
            ),
        ],
    }
    parameter = ExecutorAlternativeParameter(
        jaml_variable='JINA_DUMMY',
        choices=['pod1', 'pod2'],
        inner_parameters=inner_parameters,
        parameter_name='executoralternative',
    )

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert trial_parameters['JINA_DUMMY'] in ['pod1', 'pod2']
        if trial_parameters['JINA_DUMMY'] == 'pod1':
            assert 'JINA_INTEGER_DUMMY_POD1' in trial_parameters.keys()
            assert 0 <= trial_parameters['JINA_INTEGER_DUMMY_POD1'] <= 10
            assert 'JINA_CAT_DUMMY_POD1' in trial_parameters.keys()
            assert trial_parameters['JINA_CAT_DUMMY_POD1'] in [
                f'choice-{i}' for i in range(10)
            ]
        if trial_parameters['JINA_DUMMY'] == 'pod2':
            assert 'JINA_INTEGER_DUMMY_POD2' in trial_parameters.keys()
            assert 0 <= trial_parameters['JINA_INTEGER_DUMMY_POD2'] <= 10
            assert 'JINA_CAT_DUMMY_POD2' in trial_parameters.keys()
            assert trial_parameters['JINA_CAT_DUMMY_POD2'] in [
                f'choice-{i}' for i in range(10)
            ]

        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)

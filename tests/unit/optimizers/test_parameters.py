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
    search_space = parameter.search_space
    assert 'JINA_DUMMY' in search_space
    assert len(search_space['JINA_DUMMY']) == 11

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
    _raised = False
    try:
        _ = parameter.search_space
    except NotImplementedError:
        _raised = True
    assert _raised

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
    _raised = False
    try:
        _ = parameter.search_space
    except NotImplementedError:
        _raised = True
    assert _raised

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
    search_space = parameter.search_space
    assert 'JINA_DUMMY' in search_space
    assert len(search_space['JINA_DUMMY']) == 10

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
    search_space = parameter.search_space
    assert 'JINA_DUMMY' in search_space
    assert len(search_space['JINA_DUMMY']) == 11

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
        'executor1': [
            IntegerParameter(
                jaml_variable='JINA_INTEGER_DUMMY_EXECUTOR1',
                high=10,
                low=0,
                parameter_name='integerparam_executor1',
            ),
            CategoricalParameter(
                jaml_variable='JINA_CAT_DUMMY_EXECUTOR1',
                choices=[f'choice-{i}' for i in range(10)],
                parameter_name='categorical_executor1',
            ),
        ],
        'executor2': [
            IntegerParameter(
                jaml_variable='JINA_INTEGER_DUMMY_EXECUTOR2',
                high=10,
                low=0,
                parameter_name='integerparam_executor2',
            ),
            CategoricalParameter(
                jaml_variable='JINA_CAT_DUMMY_EXECUTOR2',
                choices=[f'choice-{i}' for i in range(10)],
                parameter_name='categorical_executor2',
            ),
        ],
    }
    parameter = ExecutorAlternativeParameter(
        jaml_variable='JINA_DUMMY',
        choices=['executor1', 'executor2'],
        inner_parameters=inner_parameters,
        parameter_name='executoralternative',
    )
    search_space = parameter.search_space
    assert 'JINA_DUMMY' in search_space
    assert 'JINA_INTEGER_DUMMY_EXECUTOR1' in search_space
    assert 'JINA_CAT_DUMMY_EXECUTOR1' in search_space
    assert 'JINA_INTEGER_DUMMY_EXECUTOR2' in search_space
    assert 'JINA_CAT_DUMMY_EXECUTOR2' in search_space
    assert len(search_space['JINA_DUMMY']) == 2
    assert len(search_space['JINA_INTEGER_DUMMY_EXECUTOR1']) == 11
    assert len(search_space['JINA_CAT_DUMMY_EXECUTOR1']) == 10
    assert len(search_space['JINA_INTEGER_DUMMY_EXECUTOR2']) == 11
    assert len(search_space['JINA_CAT_DUMMY_EXECUTOR2']) == 10

    def objective(trial):
        trial_parameters = {}
        parameter.update_trial_params(trial, trial_parameters)
        assert 'JINA_DUMMY' in trial_parameters.keys()
        assert trial_parameters['JINA_DUMMY'] in ['executor1', 'executor2']
        if trial_parameters['JINA_DUMMY'] == 'executor1':
            assert 'JINA_INTEGER_DUMMY_EXECUTOR1' in trial_parameters.keys()
            assert 0 <= trial_parameters['JINA_INTEGER_DUMMY_EXECUTOR1'] <= 10
            assert 'JINA_CAT_DUMMY_EXECUTOR1' in trial_parameters.keys()
            assert trial_parameters['JINA_CAT_DUMMY_EXECUTOR1'] in [
                f'choice-{i}' for i in range(10)
            ]
        if trial_parameters['JINA_DUMMY'] == 'executor2':
            assert 'JINA_INTEGER_DUMMY_EXECUTOR2' in trial_parameters.keys()
            assert 0 <= trial_parameters['JINA_INTEGER_DUMMY_EXECUTOR2'] <= 10
            assert 'JINA_CAT_DUMMY_EXECUTOR2' in trial_parameters.keys()
            assert trial_parameters['JINA_CAT_DUMMY_EXECUTOR2'] in [
                f'choice-{i}' for i in range(10)
            ]

        return 0.0

    study = optuna.create_study(direction='maximize', sampler=optuna_sampler)
    study.optimize(objective, n_trials=5)

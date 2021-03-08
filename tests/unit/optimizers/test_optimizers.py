import os
import optuna
import pytest
from unittest.mock import Mock
import yaml

from jina.optimizers import MeanEvaluationCallback, ResultProcessor, FlowOptimizer
from jina.optimizers.parameters import (
    IntegerParameter,
    UniformParameter,
    LogUniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
)


@pytest.fixture
def responses():
    responses = Mock()

    doc1 = Mock()
    eval1 = Mock()
    eval1.op_name = 'metric1'
    eval1.value = 1
    eval2 = Mock()
    eval2.op_name = 'metric2'
    eval2.value = 0.5
    doc1.evaluations = [eval1, eval2]

    doc2 = Mock()
    eval3 = Mock()
    eval3.op_name = 'metric1'
    eval3.value = 0.5
    eval4 = Mock()
    eval4.op_name = 'metric2'
    eval4.value = 0.5
    doc2.evaluations = [eval3, eval4]

    responses.search.docs = [doc1, doc2]
    return responses


def test_evaluation_callback_no_name(responses):
    # test with no metric name given to callback
    cb = MeanEvaluationCallback()
    cb(responses)
    cb(responses)

    evaluation = cb.get_final_evaluation()
    assert evaluation == 0.75


def test_evaluation_callback_with_name(responses):
    # test with metric name given to callback
    evaluation_metric = 'metric2'
    cb = MeanEvaluationCallback(evaluation_metric)
    cb(responses)
    cb(responses)

    evaluation = cb.get_final_evaluation()
    assert evaluation == 0.5


def test_result_processor(tmpdir):
    study = Mock()
    study.trials = [1, 2]
    study.best_trial.params = {'a': 1}
    study.best_trial.duration = 3

    filepath = os.path.join(tmpdir, 'best_config.yml')
    proc = ResultProcessor(study)
    proc.save_parameters(filepath)
    assert yaml.load(open(filepath), Loader=yaml.Loader) == {'a': 1}


def test_suggest(tmpdir):
    def _objective(trial):

        value = FlowOptimizer._suggest(
            IntegerParameter(0, 3, 1, jaml_variable='IntegerParameter'), trial
        )
        assert 0 <= value
        assert value <= 3
        value = FlowOptimizer._suggest(
            UniformParameter(0, 3, jaml_variable='UniformParameter'), trial
        )
        assert 0 <= value
        assert value <= 3
        value = FlowOptimizer._suggest(
            LogUniformParameter(1, 3, jaml_variable='LogUniformParameter'), trial
        )
        assert 1 <= value
        assert value <= 3
        value = FlowOptimizer._suggest(
            CategoricalParameter([0, 1.5, 2, 3], jaml_variable='CategoricalParameter'),
            trial,
        )
        assert 0 <= value
        assert value <= 3
        value = FlowOptimizer._suggest(
            DiscreteUniformParameter(0, 3, 1, jaml_variable='DiscreteUniformParameter'),
            trial,
        )
        assert 0 <= value
        assert value <= 3

    study = optuna.create_study()
    study.optimize(_objective, n_trials=1)

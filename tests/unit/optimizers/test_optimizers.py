import os

import pytest
from unittest.mock import Mock
import yaml

from jina.optimizers import EvaluationCallback, OptunaResultProcessor


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
    cb = EvaluationCallback()
    cb(responses)
    cb(responses)

    evaluation = cb.get_mean_evaluation()
    eval_name = list(evaluation)[0]
    assert eval_name == 'metric1'

    score = evaluation[eval_name]
    assert score == 0.75


def test_evaluation_callback_with_name(responses):
    # test with metric name given to callback
    evaluation_metric = 'metric2'
    cb = EvaluationCallback(evaluation_metric)
    cb(responses)
    cb(responses)

    evaluation = cb.get_mean_evaluation()
    eval_name = list(evaluation)[0]
    assert eval_name == evaluation_metric

    score = evaluation[eval_name]
    assert score == 0.5


def test_optuna_result_processor(tmpdir):
    study = Mock()
    study.trials = [1, 2]
    study.best_trial.params = {'a': 1}
    study.best_trial.duration = 3

    filepath = os.path.join(tmpdir, 'best_config.yml')
    proc = OptunaResultProcessor(study)
    proc.save_parameters(filepath)
    assert yaml.load(open(filepath), Loader=yaml.Loader) == {'a': 1}

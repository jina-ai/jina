from jina.executors.evaluators.rank import BaseRankingEvaluator
from jina.drivers.evaluate import RankEvaluateDriver


class DummyRankingEvaluator(BaseRankingEvaluator):
    def evaluate(self, actual, desired, *args, **kwargs) -> float:
        return 1.0


def test_base_ranking_evalutor():
    evaluator = DummyRankingEvaluator()
    actual_eval_driver = evaluator._drivers['SearchRequest'][-1]
    assert isinstance(actual_eval_driver, RankEvaluateDriver)
    default_eval_driver = RankEvaluateDriver()
    assert list(default_eval_driver.fields) == actual_eval_driver.fields
    # make sure the default value for fields in RankEvaluateDriver is no longer overwritten by `executors.requests.BaseRankingEvaluator.yml`
    from jina.jaml import JAML
    from pkg_resources import resource_filename

    with open(
        resource_filename(
            'jina',
            '/'.join(('resources', 'executors.requests.BaseRankingEvaluator.yml')),
        )
    ) as fp:
        config_from_resources = JAML.load(fp)
    assert (
        default_eval_driver.fields
        == config_from_resources['on']['SearchRequest']['drivers'][-1].fields
    )

import numpy as np

from jina.executors.evaluators.running_stats import RunningStats


def test_running_stats():
    a = np.random.random([50])
    r = RunningStats()

    for aa in a:
        r += aa

    np.testing.assert_almost_equal(a.mean(), r.mean)
    np.testing.assert_almost_equal(a.std(), r.std)

    print(str(r))

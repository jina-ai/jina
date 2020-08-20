from jina.executors.encoders.helper import reduce_mean
import numpy as np
from tests import JinaTestCase


class HelperTestCases(JinaTestCase):

    def test_reduce_mean_with_correct_input(self):
        correct_data = np.random.rand(10, 10, 3)
        correct_mask = np.random.rand(10, 10)
        correct_mean = reduce_mean(correct_data, correct_mask)
        assert type(correct_mean).__name__ == 'ndarray'

    def test_reduce_mean_with_wrong_input(self):
        wrong_data = np.random.rand(10, 10)
        correct_mask = np.random.rand(10, 10)
        with self.assertRaises(Exception) as context:
            reduce_mean(wrong_data, correct_mask)
        self.assertTrue('tuple index out of range' in str(context.exception))

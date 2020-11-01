import numpy as np

from jina.drivers.predict import BinaryPredictDriver, OneHotPredictDriver, MultiLabelPredictDriver


def test_binary_predict_driver():
    driver = BinaryPredictDriver()

    assert driver.prediction2label(np.array([0, 1, 1, 0])) == ['no', 'yes', 'yes', 'no']


def test_one_hot_predict_driver():
    driver = OneHotPredictDriver(labels=['cat', 'dog', 'human'])

    assert driver.prediction2label(np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])) == ['human', 'cat', 'dog']

    driver = OneHotPredictDriver(labels=['yes', 'no'])

    assert driver.prediction2label(np.array([[0, 1], [1, 0], [0, 1]])) == ['no', 'yes', 'no']


def test_multi_label_predict_driver():
    driver = MultiLabelPredictDriver(labels=['cat', 'dog', 'human'])

    assert driver.prediction2label(np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])) == [['human'], ['cat'], ['dog']]

    assert driver.prediction2label(np.array([[0, 1, 1], [1, 1, 0], [1, 1, 1]])) == [['dog', 'human'], ['cat', 'dog'],

                                                                                    ['cat', 'dog', 'human']]

import numpy as np

from jina.drivers.predict import BinaryPredictDriver


def test_binary_predict_driver():
    driver = BinaryPredictDriver()

    assert driver.prediction2label(np.array([0, 1, 1, 0])) == ['no', 'yes', 'yes', 'no']

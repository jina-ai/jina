import warnings

import pytest

from jina import Flow


def test_load_config_instance():
    with pytest.warns(UserWarning):  # assert that a warning has been emited
        f = Flow().load_config('config.yaml')


def test_load_config_class():  # assert that no warnings were emited
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        f = Flow.load_config('config.yaml')

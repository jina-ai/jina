import pytest


@pytest.fixture(scope='function')
def check_callback_called():
    class Called:
        def __init__(self):
            self._callback_called = False

    called = Called
    yield called
    assert called



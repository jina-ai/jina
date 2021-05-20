import os

import pytest


@pytest.fixture(autouse=True)
def setup_hellworld_env(tmpdir):
    os.environ['HW_WORKDIR'] = str(tmpdir)
    yield
    os.environ.pop("HW_WORKDIR")

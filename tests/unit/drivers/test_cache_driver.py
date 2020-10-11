import os

import pytest

from jina.drivers.cache import BloomFilterDriver, EnvBloomFilterDriver
from tests import random_docs


@pytest.mark.parametrize('num_hash', [4, 8])
def test_cache_driver_twice(num_hash):
    docs = list(random_docs(10))
    driver = BloomFilterDriver(num_hash=num_hash)
    driver._apply_all(docs)

    with pytest.raises(NotImplementedError):
        # duplicate docs
        driver._apply_all(docs)

    # new docs
    docs = list(random_docs(10))
    driver._apply_all(docs)


@pytest.mark.parametrize('num_hash', [4, 8])
def test_cache_driver_env(num_hash):
    docs = list(random_docs(10))
    driver = EnvBloomFilterDriver(num_hash=num_hash)
    assert os.environ.get(driver._env_name, None) is None
    driver._apply_all(docs)

    with pytest.raises(NotImplementedError):
        # duplicate docs
        driver._apply_all(docs)

    # now start a new one
    # should fail again, as bloom filter is persisted in os.env
    with pytest.raises(NotImplementedError):
        driver = EnvBloomFilterDriver(num_hash=num_hash)
        driver._apply_all(docs)

    assert os.environ.get(driver._env_name, None) is not None
    print(os.environ.pop(driver._env_name))

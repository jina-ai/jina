import pickle
from threading import Lock

import pytest

from jina.serve.executors import BaseExecutor


class NotSerialisable:
    def __init__(self):
        self.lock = Lock()


def test_object_not_seri():
    with pytest.raises(TypeError):
        serialized = pickle.dumps(NotSerialisable())


def test_runtime_args_not_serialisable():

    param = NotSerialisable()

    b = BaseExecutor.load_config(
        'BaseExecutor',
        runtime_args={'hello': 'world', 'not_seri': param},
    )

    assert b.runtime_args.hello == 'world'
    assert b.runtime_args.not_seri is param

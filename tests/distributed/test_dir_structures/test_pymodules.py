import os
from posixpath import join

import pytest

from daemon.clients import JinaDClient
from jina import Flow, Document, __default_host__

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
cur_dir = os.path.dirname(os.path.abspath(__file__))
jinad_client = JinaDClient(host=__default_host__, port=8000)


"""
Upload executors in Flow syntax to JinaD

executor1: (Simplest case) Single python file
.
├── executor1
│   ├── config.yml
│   └── my_executor.py

executor2: Multiple python files in one directory
.
├── executor2
│   ├── config.yml
│   └── executor
│       ├── __init__.py
│       ├── helper.py
│       └── my_executor.py

executor3: Multiple python files in multiple directories
.
├── executor3
│   ├── config.yml
│   └── executor
│       ├── __init__.py
│       ├── helper.py
│       ├── my_executor.py
│       └── utils
│           ├── __init__.py
│           ├── data.py
│           └── io.py
"""


@pytest.mark.parametrize(
    'config_yml',
    ('executor1/config.yml', 'executor2/config.yml', 'executor3/config.yml'),
)
def test_remote_executor_via_yaml_relative_path(config_yml):
    f = Flow().add(
        # host=CLOUD_HOST,
        uses=config_yml
    )
    with f:
        resp = f.post(
            on='/',
            inputs=Document(text=config_yml),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == config_yml * 2


@pytest.mark.parametrize(
    'config_yml',
    (
        os.path.join(cur_dir, 'executor1/config.yml'),
        os.path.join(cur_dir, 'executor2/config.yml'),
        os.path.join(cur_dir, 'executor3/config.yml'),
    ),
)
def test_remote_executor_via_yaml_absolute_path(config_yml):
    f = Flow().add(
        # host=CLOUD_HOST,
        uses=config_yml
    )
    with f:
        resp = f.post(
            on='/',
            inputs=Document(text=config_yml),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == config_yml * 2


@pytest.mark.parametrize(
    'executor_entrypoint',
    (
        'executor1/my_executor.py',
        'executor2/executor/__init__.py',
        'executor3/executor/__init__.py',
    ),
)
def test_remote_executor_via_pymodules_relative_path(executor_entrypoint):
    f = Flow().add(
        # host=CLOUD_HOST,
        uses='MyExecutor',
        py_modules=executor_entrypoint,
    )
    with f:
        resp = f.post(
            on='/',
            inputs=Document(text=executor_entrypoint),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == executor_entrypoint * 2


@pytest.mark.parametrize(
    'executor_entrypoint',
    (
        os.path.join(cur_dir, 'executor1/my_executor.py'),
        os.path.join(cur_dir, 'executor2/executor/__init__.py'),
        os.path.join(cur_dir, 'executor3/executor/__init__.py'),
    ),
)
def test_remote_executor_via_pymodules_absolute_path(executor_entrypoint):
    f = Flow().add(
        # host=CLOUD_HOST,
        uses='MyExecutor',
        py_modules=executor_entrypoint,
    )
    with f:
        resp = f.post(
            on='/',
            inputs=Document(text=executor_entrypoint),
            return_results=True,
        )
        assert resp[0].data.docs[0].text == executor_entrypoint * 2

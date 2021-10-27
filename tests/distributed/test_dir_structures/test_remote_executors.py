import os

import pytest
from jina import Flow, Document, __default_host__

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
cur_dir = os.path.dirname(os.path.abspath(__file__))

"""
Upload executors in `Flow().add()` syntax to JinaD

src1: (Simplest case) Single python file
.
├── src1
│   ├── config.yml
│   └── my_executor.py

src2: Multiple python files in one directory
.
├── src2
│   ├── config.yml
│   └── executors
│       ├── __init__.py
│       ├── helper.py
│       └── my_executor.py

src3: Multiple python files in multiple directories
.
├── src3
│   ├── config.yml
│   └── executors
│       ├── __init__.py
│       ├── helper.py
│       ├── my_executor.py
│       └── utils
│           ├── __init__.py
│           ├── data.py
│           └── io.py

src4: Multiple Executors using python files in multiple directories
.
├── src4
│   ├── config_data.yml
│   ├── config_io.yml
│   └── executors
│       ├── __init__.py
│       ├── helper.py
│       ├── my_executor.py      # Multiple Executors
│       └── utils
│           ├── __init__.py
│           ├── data.py
│           └── io.py
"""


@pytest.mark.parametrize(
    'config_yml',
    ('src1/config.yml', 'src2/config.yml', 'src3/config.yml', 'src4/config.yml'),
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
        os.path.join(cur_dir, 'src1/config.yml'),
        os.path.join(cur_dir, 'src2/config.yml'),
        os.path.join(cur_dir, 'src3/config.yml'),
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
        'src1/executor.py',
        'src2/executors/__init__.py',
        'src3/executors/__init__.py',
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
        os.path.join(cur_dir, 'src1/executor.py'),
        os.path.join(cur_dir, 'src2/executors/__init__.py'),
        os.path.join(cur_dir, 'src3/executors/__init__.py'),
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

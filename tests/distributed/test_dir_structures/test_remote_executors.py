import os

import pytest
from jina import Flow, Document, Client, __default_host__

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
cur_dir = os.path.dirname(os.path.abspath(__file__))
exposed_port = 12345

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

src5: Multiple python files in multiple directories with custom dependencies
.
├── src5
│   ├── config.yml
│   └── executors
│       ├── __init__.py
│       ├── helper.py
│       ├── my_executor.py
│       └── utils
│           ├── __init__.py
│           ├── data.py
│           └── io.py
│   ├── flow.yml
│   ├── requirements-index.txt
│   ├── requirements.txt

"""


@pytest.mark.parametrize(
    'upload_files, config_yml',
    [
        ('src1', 'config.yml'),
        ('src2', 'config.yml'),
        ('src3', 'config.yml'),
        ('src4', 'config_data.yml'),
        ('src4', 'config_io.yml'),
        ('src5', 'config.yml'),
        (os.path.join(cur_dir, 'src1'), 'config.yml'),
        (os.path.join(cur_dir, 'src2'), 'config.yml'),
        (os.path.join(cur_dir, 'src3'), 'config.yml'),
        (os.path.join(cur_dir, 'src4'), 'config_data.yml'),
        (os.path.join(cur_dir, 'src4'), 'config_io.yml'),
        (os.path.join(cur_dir, 'src5'), 'config.yml'),
    ],
)
def test_remote_executor_via_config_yaml(upload_files, config_yml):
    f = Flow(port_expose=exposed_port).add(
        host=CLOUD_HOST, uses=config_yml, upload_files=upload_files
    )
    with f:
        resp = Client(port=exposed_port).post(
            on='/',
            inputs=Document(text=config_yml),
            return_results=True,
        )
    assert resp[0].data.docs[0].text == config_yml * 2


@pytest.mark.parametrize(
    'upload_files, uses, py_modules',
    [
        ('src1', 'MyExecutor', 'my_executor.py'),
        ('src2', 'MyExecutor', 'executors/__init__.py'),
        ('src3', 'MyExecutor', 'executors/__init__.py'),
        ('src4', 'IOExecutor', 'executors/__init__.py'),
        ('src4', 'DataExecutor', 'executors/__init__.py'),
        ('src5', 'MyExecutor', 'executors/__init__.py'),
        (os.path.join(cur_dir, 'src1'), 'MyExecutor', 'my_executor.py'),
        (os.path.join(cur_dir, 'src2'), 'MyExecutor', 'executors/__init__.py'),
        (os.path.join(cur_dir, 'src3'), 'MyExecutor', 'executors/__init__.py'),
        (os.path.join(cur_dir, 'src4'), 'IOExecutor', 'executors/__init__.py'),
        (os.path.join(cur_dir, 'src4'), 'DataExecutor', 'executors/__init__.py'),
        (os.path.join(cur_dir, 'src5'), 'MyExecutor', 'executors/__init__.py'),
    ],
)
def test_remote_executor_via_pymodules(upload_files, uses, py_modules):
    f = Flow(port_expose=exposed_port).add(
        host=CLOUD_HOST,
        uses=uses,
        py_modules=py_modules,
        upload_files=upload_files,
    )
    with f:
        resp = Client(port=exposed_port).post(
            on='/',
            inputs=Document(text=py_modules),
            return_results=True,
        )
    assert resp[0].data.docs[0].text == py_modules * 2

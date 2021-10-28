import os
import asyncio
from pathlib import Path

from jina import __resources_path__
from jina.parsers import set_pea_parser
from jina.peapods.runtimes.jinad import JinadRuntime

import pytest

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    'upload_files, uses, py_modules',
    [
        ('executor', 'MyExecutor', 'my_executor.py'),
        (os.path.join(cur_dir, 'executor'), 'MyExecutor', 'my_executor.py'),
        ('executor', 'config.yml', ''),
        (os.path.join(cur_dir, 'executor'), 'config.yml', ''),
    ],
)
def test_mask_args_py_module(upload_files, uses, py_modules, monkeypatch):
    monkeypatch.setattr(JinadRuntime, 'async_setup', lambda *args: asyncio.sleep(0.1))
    args = set_pea_parser().parse_args(
        [
            '--uses',
            uses,
            '--py-modules',
            py_modules,
            '--upload-files',
            upload_files,
            '--log-config',
            os.path.join(__resources_path__, 'logging.quiet.yml'),
        ]
    )
    runtime = JinadRuntime(args=args)
    assert runtime.filepaths == [Path(os.path.join(cur_dir, 'executor'))]
    newargs = runtime._mask_args()
    assert newargs.uses == uses
    assert newargs.py_modules == [py_modules]
    assert newargs.disable_remote == True
    assert newargs.upload_files == []
    assert newargs.log_config == ''
    assert newargs.noblock_on_start == False

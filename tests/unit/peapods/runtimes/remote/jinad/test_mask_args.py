import os
import asyncio
from contextlib import nullcontext
from pathlib import Path

from jina.parsers import set_pea_parser
from jina.peapods.runtimes.jinad import JinadRuntime
from daemon.helper import change_cwd

import pytest

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    'uses, py_modules, directory',
    (
        ['MyExecutor', 'my_executor.py', os.path.join(cur_dir, 'executor')],
        ['MyExecutor', 'executor/my_executor.py', None],
        ['MyExecutor', os.path.join(cur_dir, 'executor', 'my_executor.py'), None],
    ),
)
def test_mask_args_py_module(uses, py_modules, directory, monkeypatch):
    ctx = change_cwd(directory) if directory else nullcontext()
    with ctx:
        monkeypatch.setattr(
            JinadRuntime, 'async_setup', lambda *args: asyncio.sleep(0.1)
        )
        args = set_pea_parser().parse_args(['--uses', uses, '--py-modules', py_modules])
        runtime = JinadRuntime(args=args)
        newargs = runtime._mask_args()
        assert newargs.uses == uses
        assert newargs.py_modules == ['executor/my_executor.py']
        assert len(runtime._filepaths) == 1
        assert runtime._filepaths[0] == Path(os.path.join(cur_dir, 'executor'))


@pytest.mark.parametrize(
    'uses, directory',
    (
        ['config.yml', os.path.join(cur_dir, 'executor')],
        ['executor/config.yml', None],
        [os.path.join(cur_dir, 'executor', 'config.yml'), None],
    ),
)
def test_mask_args_config_yml(uses, directory, monkeypatch):
    ctx = change_cwd(directory) if directory else nullcontext()
    with ctx:
        monkeypatch.setattr(
            JinadRuntime, 'async_setup', lambda *args: asyncio.sleep(0.1)
        )
        args = set_pea_parser().parse_args(['--uses', uses])
        runtime = JinadRuntime(args=args)
        newargs = runtime._mask_args()
        assert newargs.uses == 'executor/config.yml'
        assert len(runtime._filepaths) == 1
        assert runtime._filepaths[0] == Path(os.path.join(cur_dir, 'executor'))

"""Tests that flow can launch when using the spawn multiprocessing method

Currently when using class name this still breaks (see xfail)
"""

import os
import subprocess
import sys
from pathlib import Path


import pytest


def test_launch_spawn_empty():
    subprocess.run(
        [sys.executable, 'main_empty.py'],
        check=True,
        env={'JINA_MP_START_METHOD': 'spawn', 'PATH': os.environ['PATH']},
        cwd=Path(__file__).parent / 'modules',
    )


def test_launch_spawn_cls():
    print(sys.executable)
    subprocess.run(
        [sys.executable, 'main_cls.py'],
        check=True,
        env={'JINA_MP_START_METHOD': 'spawn', 'PATH': os.environ['PATH']},
        cwd=Path(__file__).parent / 'modules',
    )


@pytest.mark.xfail(reason="re-importing not possible when given only exec name")
def test_launch_spawn_name():
    subprocess.run(
        [sys.executable, 'main_name.py'],
        check=True,
        env={'JINA_MP_START_METHOD': 'spawn', 'PATH': os.environ['PATH']},
        cwd=Path(__file__).parent / 'modules',
    )

"""Tests that flow can launch when using the spawn multiprocessing method"""

import os
import subprocess
import sys
from pathlib import Path


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


def test_launch_spawn_name():
    subprocess.run(
        [sys.executable, 'main_name.py'],
        check=True,
        env={'JINA_MP_START_METHOD': 'spawn', 'PATH': os.environ['PATH']},
        cwd=Path(__file__).parent / 'modules',
    )


def test_launch_spawn_jaml():
    subprocess.run(
        [sys.executable, 'main_jaml.py'],
        check=True,
        env={'JINA_MP_START_METHOD': 'spawn', 'PATH': os.environ['PATH']},
        cwd=Path(__file__).parent / 'modules',
    )

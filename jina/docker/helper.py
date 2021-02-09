"""Module for helper functions for Docker."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from pathlib import Path


def credentials_file() -> Path:
    """
    Get path to credentials file.

    :return: the path
    """
    Path.home().joinpath('.jina').mkdir(parents=True, exist_ok=True)
    return Path.home().joinpath('.jina').joinpath('access.yml')

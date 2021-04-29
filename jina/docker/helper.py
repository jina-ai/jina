"""Module for helper functions for Docker."""

from pathlib import Path


def credentials_file() -> Path:
    """
    Get path to credentials file.

    :return: the path
    """
    Path.home().joinpath('.jina').mkdir(parents=True, exist_ok=True)
    return Path.home().joinpath('.jina').joinpath('access.yml')

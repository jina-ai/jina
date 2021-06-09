"""Module for helper functions for Docker."""

import io
import ast
from typing import List
from pathlib import Path


def credentials_file() -> Path:
    """
    Get path to credentials file.

    :return: the path
    """
    Path.home().joinpath('.jina').mkdir(parents=True, exist_ok=True)
    return Path.home().joinpath('.jina').joinpath('access.yml')


def inspect_executors(py_modules: List[Path]):
    """
    Inspect executors defined by given py_modules

    :param py_modules: the list of py modules
    :return: the list of executors
    """

    def _inspect_class_defs(tree):
        return [o for o in ast.walk(tree) if isinstance(o, ast.ClassDef)]

    classes = []
    for filepath in py_modules:
        with filepath.open() as fin:
            tree = ast.parse(fin.read(), filename=str(filepath))
            classes.extend([(c, filepath) for c in _inspect_class_defs(tree)])

    # class_names = [c.name for c, _ in classes]

    executors = []
    for classdef, filepath in classes:
        for base_class in classdef.bases:
            # if the class looks like class MyExecutor(Executor)
            if isinstance(base_class, ast.Name):
                base_name = base_class.id
            # if the class looks like class MyExecutor(jina.Executor):
            if isinstance(base_class, ast.Attribute):
                base_name = base_class.attr
            if base_name == 'Executor':
                executors.append((classdef.name, filepath))

    return executors


def archive_package(package_folder: 'Path') -> 'io.BytesIO':
    """
    Archives the given folder in zip format and return a data stream.

    :param package_folder: the folder path of the package
    :return: the data stream of zip content
    """
    import os
    import zipfile

    import pathspec

    # TODO: get ignored file pattern from `resources/ignored_files`
    ignored_file_specs = ['**/*.pyc']
    ignored_dir_specs = [
        '__MACOSX',
        '.DS_Store',
        '__pycache__',
        '.eggs',
        '*.egg-info',
        '.git',
        '.vscode',
    ]
    ignored_specs = ignored_file_specs + ignored_dir_specs

    ignored_spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern, ignored_specs
    )

    zip_stream = io.BytesIO()
    try:
        zfile = zipfile.ZipFile(zip_stream, 'w', compression=zipfile.ZIP_DEFLATED)
    except EnvironmentError as e:
        raise e

    def _zip(base_path, path, archive):
        paths = os.listdir(path)
        for p in paths:
            if ignored_spec.match_file(p):
                continue
            p = os.path.join(path, p)
            if os.path.isdir(p):
                _zip(base_path, p, archive)
            else:
                archive.write(p, os.path.relpath(p, base_path))

    root_path = str(package_folder.resolve())

    _zip('', root_path, zfile)

    zfile.close()
    zip_stream.seek(0)

    return zip_stream

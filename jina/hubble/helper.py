"""Module for helper functions for Hub API."""

import io
import os
import zipfile
from pathlib import Path

from jina import __resources_path__
from jina.importer import ImportExtensions


def archive_package(package_folder: 'Path') -> 'io.BytesIO':
    """
    Archives the given folder in zip format and return a data stream.
    :param package_folder: the folder path of the package
    :return: the data stream of zip content
    """

    with ImportExtensions(required=True):
        import pathspec

    with open(os.path.join(__resources_path__, 'Python.gitignore')) as fp:
        ignored_spec = pathspec.PathSpec.from_lines('gitwildmatch', fp)

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
    _zip(root_path, root_path, zfile)

    zfile.close()
    zip_stream.seek(0)

    return zip_stream

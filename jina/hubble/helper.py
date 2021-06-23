"""Module for helper functions for Hub API."""

import io
import os
import hashlib
from typing import Tuple, Optional
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from .. import __resources_path__
from ..importer import ImportExtensions


def parse_hub_uri(uri_path: str) -> Tuple[str, str, str, str]:
    """Parse the uri of the Jina Hub executor.

    :param uri_path: the uri of Jina Hub executor
    :return: a tuple of schema, id, tag, and secret
    """
    parser = urlparse(uri_path)
    scheme = parser.scheme
    items = list(parser.netloc.split(':'))
    name = items[0]
    secret = items[1] if len(items) > 1 else None
    tag = parser.path.strip('/') if parser.path else None
    return scheme, name, tag, secret


def md5file(file_path: 'Path') -> str:
    """Retrun the MD5 checksum of the file

    :param file_path: the file to check md5sum
    :return: the MD5 checksum
    """
    hash_md5 = hashlib.md5()
    with file_path.open(mode='rb') as fp:
        for chunk in iter(lambda: fp.read(128 * hash_md5.block_size), b''):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def unpack_package(filepath: 'Path', target_dir: 'Path'):
    """Unpack the file to the target_dir.

    :param filepath: the path of given file
    :param target_dir: the path of target folder
    """
    if filepath.suffix == '.zip':
        with zipfile.ZipFile(filepath, 'r') as zip:
            zip.extractall(target_dir)
    elif filepath.suffix in ['.tar', '.gz']:
        with zipfile.open(filepath) as tar:
            tar.extractall(target_dir)
    else:
        raise ValueError("File format is not supported for unpacking.")


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


def download_with_resume(
    url: str,
    target_dir: 'Path',
    filename: Optional[str] = None,
    md5sum: Optional[str] = None,
) -> 'Path':
    """
    Download file from url to target_dir, and check md5sum.
    Performs a HTTP(S) download that can be restarted if prematurely terminated.
    The HTTP server must support byte ranges.

    :param url: the URL to download
    :param target_dir: the target path for the file
    :param filename: the filename of the downloaded file
    :param md5sum: the MD5 checksum to match

    :return: the filepath of the downloaded file
    """
    with ImportExtensions(required=True):
        import requests

    def _download(url, target, resume_byte_pos: int = None):
        resume_header = (
            {'Range': f'bytes={resume_byte_pos}-'} if resume_byte_pos else None
        )

        try:
            r = requests.get(url, stream=True, headers=resume_header)
        except requests.exceptions.RequestException as e:
            raise e

        block_size = 1024
        mode = 'ab' if resume_byte_pos else 'wb'

        with target.open(mode=mode) as f:
            for chunk in r.iter_content(32 * block_size):
                f.write(chunk)

    if filename is None:
        filename = url.split('/')[-1]
    filepath = target_dir / filename

    _resume_byte_pos = None
    if filepath.exists():
        if md5sum and md5file(filepath) == md5sum:
            return filepath
        head_info = requests.head(url)
        file_size_online = int(head_info.headers.get('content-length', 0))
        file_size_offline = filepath.stat().st_size
        if file_size_online > file_size_offline:
            _resume_byte_pos = file_size_offline
    _download(url, filepath, _resume_byte_pos)

    if md5sum and not md5file(filepath) == md5sum:
        raise RuntimeError('MD5 checksum failed.')

    return filepath

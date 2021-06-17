"""Module for helper functions for Hub API."""

import io
import os
import hashlib
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from jina import __resources_path__
from jina.importer import ImportExtensions


def md5file(file_path: 'Path') -> str:
    """Retrun the MD5 checksum of the file

    :param file_path: the file to check md5sum
    :return: the MD5 checksum
    """
    hash_md5 = hashlib.md5()
    with file_path.open(mode='rb') as f:
        for chunk in f.iter_content(chunk_size=4096):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


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
    url: str, md5sum: str, target_dir: 'Path', filename: 'Path' = None
) -> 'Path':
    """
    Download file from url to target_dir, and check md5sum.
    Performs a HTTP(S) download that can be restarted if prematurely terminated.
    The HTTP server must support byte ranges.

    :param url: the URL to download
    :param md5sum: the MD5 checksum to match
    :param target_dir: the target path for the file
    :param filename: the filename of the downloaded file

    :return: the filepath of the downloaded file
    """
    with ImportExtensions(required=True):
        import requests

    def _download(url, target, resume_byte_pos: int = None):
        resume_header = (
            {'Range': f'bytes={resume_byte_pos}-'} if resume_byte_pos else None
        )

        r = requests.get(url, stream=True, headers=resume_header)

        block_size = 1024
        mode = 'ab' if resume_byte_pos else 'wb'

        with target.open(mode=mode) as f:
            for chunk in r.iter_content(32 * block_size):
                f.write(chunk)

    if filename is None:
        filename = Path(url.split("/")[-1])
    filepath = target_dir / filename

    if not (filepath.exists() and md5file(filepath) == md5sum):
        head_info = requests.head(url)

        file_size_online = int(head_info.headers.get('content-length', 0))

        if filepath.exists():
            file_size_offline = filepath.stat().st_size
            if file_size_online > file_size_offline:
                # resume download
                _download(url, filepath, file_size_offline)
            else:
                _download(url, filepath)
        else:
            _download(url, filepath)

    if not md5file(filepath) == md5sum:
        raise RuntimeError("MD5 checksum failed.")

    return filepath


# def unpack(filepath, target_dir):
#     """Unpack the file to the target_dir."""
#     print("Unpacking %s ..." % filepath)
#     if filepath.endswith('.zip'):
#         zip = zipfile.ZipFile(filepath, 'r')
#         zip.extractall(target_dir)
#         zip.close()
#     elif filepath.endswith('.tar') or filepath.endswith('.tar.gz'):
#         tar = zipfile.open(filepath)
#         tar.extractall(target_dir)
#         tar.close()
#     else:
#         raise ValueError("File format is not supported for unpacking.")

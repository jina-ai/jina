"""Module for helper functions for Hub API."""

import hashlib
import io
import os
import shelve
import subprocess
import sys
import tarfile
import urllib
import warnings
import zipfile
from contextlib import nullcontext
from functools import lru_cache, wraps
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from jina import __cache_path__, __resources_path__
from jina.enums import BetterEnum
from jina.helper import get_request_header as _get_request_header_main
from jina.hubble.requirements import (
    check_env_variable,
    expand_env_variables,
    get_env_variables,
    parse_requirement,
)
from jina.importer import ImportExtensions
from jina.logging.predefined import default_logger


@lru_cache()
def get_hub_packages_dir() -> Path:
    """Get the path of folder where the hub packages are stored

    :return: the path of folder where the hub packages are stored
    """
    root = Path(__cache_path__)
    hub_packages = root.joinpath('hub-package')

    if not hub_packages.exists():
        hub_packages.mkdir(parents=True, exist_ok=True)

    return hub_packages


@lru_cache()
def get_cache_db() -> Path:
    """Get the path of cache db of hub Executors

    :return: the path of cache db of hub Executors
    """
    root = Path(__cache_path__)
    cache_db = root.joinpath('disk_cache.db')

    return cache_db


@lru_cache()
def get_download_cache_dir() -> Path:
    """Get the path of cache folder where the downloading cache is stored

    :return: the path of cache folder where the downloading cache is stored
    """
    cache_dir = Path(__cache_path__)

    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir


def get_request_header() -> Dict:
    """Return the header of request with an authorization token.

    :return: request header
    """
    headers = _get_request_header_main()
    import hubble

    auth_token = hubble.get_token()
    if auth_token:
        headers['Authorization'] = f'token {auth_token}'

    return headers


def parse_hub_uri(uri_path: str) -> Tuple[str, str, str, str]:
    """Parse the uri of the Jina Hub executor.

    :param uri_path: the uri of Jina Hub executor
    :return: a tuple of schema, id, tag, and secret
    """
    parser = urlparse(uri_path)
    scheme = parser.scheme
    if scheme not in {'jinahub', 'jinahub+docker', 'jinahub+sandbox'}:
        raise ValueError(f'{uri_path} is not a valid Hub URI.')

    items = list(parser.netloc.split(':'))
    name = items[0]

    if not name:
        raise ValueError(f'{uri_path} is not a valid Hub URI.')

    secret = items[1] if len(items) > 1 else None
    tag = parser.path.strip('/') if parser.path else None

    return scheme, name, tag, secret


def replace_secret_of_hub_uri(uri_path: str, txt: str = '<secret>') -> str:
    """Replace the secret of the Jina Hub URI.

    :param uri_path: the uri of Jina Hub URI
    :param txt: text to replace
    :return: the new URI
    """

    try:
        secret = parse_hub_uri(uri_path)[-1]
        if secret:
            return uri_path.replace(secret, txt)
    except ValueError:
        pass  # ignore if the URI is not a valid Jina Hub URI
    return uri_path


def is_valid_huburi(uri: str) -> bool:
    """Return True if it is a valid Hubble URI

    :param uri: the uri to test
    :return: True or False
    """
    try:
        parse_hub_uri(uri)
        return True
    except:
        return False


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
        with tarfile.open(filepath) as tar:
            tar.extractall(target_dir)
    else:
        raise ValueError('File format is not supported for unpacking.')


def archive_package(package_folder: 'Path') -> 'io.BytesIO':
    """
    Archives the given folder in zip format and return a data stream.
    :param package_folder: the folder path of the package
    :return: the data stream of zip content
    """

    with ImportExtensions(required=True):
        import pathspec

    root_path = package_folder.resolve()

    gitignore = root_path / '.gitignore'
    if not gitignore.exists():
        gitignore = Path(__resources_path__) / 'Python.gitignore'

    with gitignore.open() as fp:
        ignore_lines = [
            line.strip() for line in fp if line.strip() and (not line.startswith('#'))
        ]
        ignore_lines += ['.git', '.jina']
        ignored_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_lines)

    zip_stream = io.BytesIO()
    try:
        zfile = zipfile.ZipFile(zip_stream, 'w', compression=zipfile.ZIP_DEFLATED)
    except EnvironmentError as e:
        raise e

    def _zip(base_path, path, archive):

        for p in path.iterdir():
            rel_path = p.relative_to(base_path)
            if ignored_spec.match_file(str(rel_path)):
                continue
            if p.is_dir():
                _zip(base_path, p, archive)
            else:
                archive.write(p, rel_path)

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

    head_info = requests.head(url)
    file_size_online = int(head_info.headers.get('content-length', 0))

    _resume_byte_pos = None
    if filepath.exists():
        if md5sum and md5file(filepath) == md5sum:
            return filepath

        file_size_offline = filepath.stat().st_size
        if file_size_online > file_size_offline:
            _resume_byte_pos = file_size_offline

    _download(url, filepath, _resume_byte_pos)

    if md5sum and not md5file(filepath) == md5sum:
        raise RuntimeError(
            'MD5 checksum failed.'
            'Might happen when the network is unstable, please retry.'
            'If still not work, feel free to raise an issue.'
            'https://github.com/jina-ai/jina/issues/new'
        )

    return filepath


def upload_file(
    url: str,
    file_name: str,
    buffer_data: bytes,
    dict_data: Dict,
    headers: Dict,
    stream: bool = False,
    method: str = 'post',
):
    """Upload file to target url

    :param url: target url
    :param file_name: the file name
    :param buffer_data: the data to upload
    :param dict_data: the dict-style data to upload
    :param headers: the request header
    :param stream: receive stream response
    :param method: the request method
    :return: the response of request
    """
    with ImportExtensions(required=True):
        import requests

    dict_data.update({'file': (file_name, buffer_data)})

    (data, ctype) = requests.packages.urllib3.filepost.encode_multipart_formdata(
        dict_data
    )

    headers.update({'Content-Type': ctype})

    response = getattr(requests, method)(url, data=data, headers=headers, stream=stream)

    return response


def disk_cache_offline(
    cache_file: str = 'disk_cache.db',
    message: str = 'Calling {func_name} failed, using cached results',
):
    """
    Decorator which caches a function in disk and uses cache when a urllib.error.URLError exception is raised
    If the function was called with a kwarg force=True, then this decorator will always attempt to call it, otherwise,
    will always default to local cache.

    :param cache_file: the cache file
    :param message: the warning message shown when defaulting to cache. Use "{func_name}" if you want to print
        the function name

    :return: function decorator
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            call_hash = f'{func.__name__}({", ".join(map(str, args))})'

            pickle_protocol = 4
            file_lock = nullcontext()
            with ImportExtensions(
                required=False,
                help_text=f'FileLock is needed to guarantee non-concurrent access to the'
                f'cache_file {cache_file}',
            ):
                import filelock

                file_lock = filelock.FileLock(f'{cache_file}.lock', timeout=-1)

            cache_db = None
            with file_lock:
                try:
                    cache_db = shelve.open(
                        cache_file, protocol=pickle_protocol, writeback=True
                    )
                except Exception:
                    if os.path.exists(cache_file):
                        # cache is in an unsupported format, reset the cache
                        os.remove(cache_file)
                        cache_db = shelve.open(
                            cache_file, protocol=pickle_protocol, writeback=True
                        )

            if cache_db is None:
                # if we failed to load cache, do not raise, it is only an optimization thing
                return func(*args, **kwargs), False
            else:
                with cache_db as dict_db:
                    try:
                        if call_hash in dict_db and not kwargs.get('force', False):
                            return dict_db[call_hash], True

                        result = func(*args, **kwargs)
                        dict_db[call_hash] = result
                    except urllib.error.URLError:
                        if call_hash in dict_db:
                            default_logger.warning(
                                message.format(func_name=func.__name__)
                            )
                            return dict_db[call_hash], True
                        else:
                            raise
                return result, False

        return wrapper

    return decorator


def is_requirements_installed(
    requirements_file: 'Path', show_warning: bool = False
) -> bool:
    """Return True if requirements.txt is installed locally
    :param requirements_file: the requirements.txt file
    :param show_warning: if to show a warning when a dependency is not satisfied
    :return: True or False if not satisfied
    """
    import pkg_resources
    from pkg_resources import (
        DistributionNotFound,
        RequirementParseError,
        VersionConflict,
    )

    install_reqs, install_options = _get_install_options(requirements_file)

    if len(install_reqs) == 0:
        return True

    try:
        pkg_resources.require('\n'.join(install_reqs))
    except (DistributionNotFound, VersionConflict, RequirementParseError) as ex:
        if show_warning:
            warnings.warn(repr(ex))
        return isinstance(ex, VersionConflict)
    return True


def get_requirements_env_variables(requirements_file: 'Path') -> list:
    """get the env variables in requirements.txt
    :param requirements_file: the requirements.txt file
    :return: List of env variables in requirements.txt
    """
    env_variables = []
    with requirements_file.open() as requirements:
        for req in requirements:
            req = req.strip()
            if (not req) or req.startswith('#'):
                continue
            else:
                variables = get_env_variables(req)
                env_variables.extend(variables)

    return env_variables


def check_requirements_env_variable(env_variable: str) -> bool:
    """
    check the environment variables is limited
    to uppercase letter and number and the `_` (underscore).
    :param env_variable: env_variable in the requirements.txt file
    :return: True or False if not satisfied
    """
    return check_env_variable(env_variable)


def replace_requirements_env_variables(requirements_file: 'Path') -> list:
    """replace the environment variables in requirements.txt
    :param requirements_file: the requirements.txt file
    :return: List of replaced env variables in requirements.txt
    """
    env_variables = []
    with requirements_file.open('r') as requirements:
        for line in requirements.readlines():
            line = line.strip()
            if (not line) or line.startswith('#'):
                continue
            else:
                line = expand_env_variables(line)
                env_variables.append(line)
    return env_variables


def _get_install_options(requirements_file: 'Path', excludes: Tuple[str] = ('jina',)):
    with requirements_file.open() as requirements:
        install_options = []
        install_reqs = []
        for req in requirements:
            req = req.strip()
            if (not req) or req.startswith('#'):
                continue
            elif req.startswith('-'):
                for index, item in enumerate(req.split(' ')):
                    install_options.append(expand_env_variables(item))
            else:
                expand_req = expand_env_variables(req)
                req_spec = parse_requirement(expand_req)

                if req_spec.project_name not in excludes or len(req_spec.extras) > 0:
                    install_reqs.append(expand_req)
    return install_reqs, install_options


def install_requirements(requirements_file: 'Path', timeout: int = 1000):
    """Install modules included in requirments file
    :param requirements_file: the requirements.txt file
    :param timeout: the socket timeout (default = 1000s)
    """

    if is_requirements_installed(requirements_file):
        return

    install_reqs, install_options = _get_install_options(requirements_file)

    subprocess.check_call(
        [
            sys.executable,
            '-m',
            'pip',
            'install',
            '--compile',
            f'--default-timeout={timeout}',
        ]
        + install_reqs
        + install_options
    )


class HubbleReturnStatus(BetterEnum):
    """
    Type of hubble return status enum
    """

    UNKNOWN_ERROR = -1
    OK = 20000
    PARAM_VALIDATION_ERROR = 40001
    SQL_CREATION_ERROR = 40002
    DATA_STREAM_BROKEN_ERROR = 40003
    UNEXPECTED_MIME_TYPE_ERROR = 40004
    SSO_LOGIN_REQUIRED = 40101
    AUTHENTICATION_FAILED = 40102
    AUTHENTICATION_REQUIRED = 40103
    OPERATION_NOT_ALLOWED = 40301
    INTERNAL_RESOURCE_NOT_FOUND = 40401
    RPC_METHOD_NOT_FOUND = 40402
    REQUESTED_ENTITY_NOT_FOUND = 40403
    INTERNAL_RESOURCE_METHOD_NOT_ALLOWED = 40501
    INCOMPATIBLE_METHOD_ERROR = 40502
    INTERNAL_RESOURCE_ID_CONFLICT = 40901
    RESOURCE_POLICY_DENY = 40902
    TOO_LARGE_FILE = 41301
    INTERNAL_DATA_CORRUPTION = 42201
    IDENTIFIER_NAMESPACE_OCCUPIED = 42202
    SUBMITTED_DATA_MALFORMED = 42203
    EXTERNAL_SERVICE_FAILURE = 42204
    DOWNSTREAM_SERVICE_FAILURE = 42205
    SERVER_INTERNAL_ERROR = 50001
    DOWNSTREAM_SERVICE_ERROR = 50002
    SERVER_SUBPROCESS_ERROR = 50003
    SANDBOX_BUILD_NOT_FOUND = 50004
    NOT_IMPLEMENTED_ERROR = 50005
    RESPONSE_STREAM_CLOSED = 50006


class NormalizerErrorCode(BetterEnum):
    """
    Type of executor-normalizer error code enum
    """

    ExecutorNotFound = 4000
    ExecutorExists = 4001
    IllegalExecutor = 4002
    BrokenDependency = 4003

    Others = 5000


def get_hubble_error_message(hubble_structured_error: dict) -> Tuple[str, str]:
    """Override some of the hubble error messages to provide better user experience
    :param hubble_structured_error: the hubble structured error response
    :returns: Tuple of overridden_msg and original_msg
    """
    msg = hubble_structured_error.get(
        'readableMessage', ''
    ) or hubble_structured_error.get('message', '')
    status = hubble_structured_error.get('status', None)
    original_msg = msg

    if not status:
        return (msg, msg)

    if (
        status == HubbleReturnStatus.SERVER_SUBPROCESS_ERROR
        and hubble_structured_error.get('cmd', '') == 'docker'
    ):

        msg = '''
Failed on building Docker image. Potential solutions:
  - If you haven't provide a Dockerfile in the executor bundle, you may want to provide one,
    as the auto-generated one on the cloud did not work.
  - If you have provided a Dockerfile, you may want to check the validity of this Dockerfile.
'''
    elif (
        status == HubbleReturnStatus.DOWNSTREAM_SERVICE_FAILURE
        and hubble_structured_error.get('service', '') == 'normalizer'
    ):

        normalizer_error = hubble_structured_error.get('err', '')
        if (
            isinstance(normalizer_error, dict)
            and normalizer_error.get('code', None)
            == NormalizerErrorCode.ExecutorNotFound
        ):
            msg = '''
We can not discover any Executor in your uploaded bundle. This is often due to one of the following errors:
  - The bundle did not contain any valid executor.
  - The config.yml's `jtype` is mismatched with the actual Executor class name.
    For more information about the expected bundle structure, please refer to the documentation.
    https://docs.jina.ai/fundamentals/executor/executor-files/#multiple-python-files-yaml 
'''
        msg += '''
For more detailed information, you can try the `executor-normalizer` locally to see the root cause.
    https://github.com/jina-ai/executor-normalizer
'''

    return (msg, original_msg)

"""Module wrapping interactions with the local executor packages."""

import json
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional

from . import HubExecutor
from .helper import unpack_package, install_requirements
from ..helper import random_identity

_hub_root = Path(
    os.environ.get('JINA_HUB_ROOT', Path.home().joinpath('.jina', 'hub-packages'))
)
_hub_root.mkdir(parents=True, exist_ok=True)


def get_dist_path(uuid: str, tag: str) -> Tuple['Path', 'Path']:
    """Get the package path according ID and TAG
    :param uuid: the UUID of the executor
    :param tag: the TAG of the executor
    :return: package and its dist-info path
    """
    pkg_path = _hub_root / uuid
    pkg_dist_path = _hub_root / f'{uuid}-{tag}.dist-info'
    return pkg_path, pkg_dist_path


def get_config_path(local_id: str) -> 'Path':
    """Get the local configure file
    :param local_id: the random local ID of the executor
    :return: json config path
    """
    return _hub_root / f'{local_id}.json'


def get_lockfile() -> str:
    """Get the path of file locker
    :return: the path of file locker
    """
    return str(_hub_root / 'LOCK')


def load_secret(work_path: 'Path') -> Tuple[str, str]:
    """Get the UUID and Secret from local

    :param work_path: the local package directory
    :return: the UUID and secret
    """
    from cryptography.fernet import Fernet

    config = work_path / '.jina'
    config.mkdir(parents=True, exist_ok=True)

    local_id_file = config / 'secret.key'
    uuid8 = None
    secret = None
    if local_id_file.exists():
        with local_id_file.open() as f:
            local_id, local_key = f.readline().strip().split('\t')
            fernet = Fernet(local_key.encode())

        local_config_file = get_config_path(local_id)
        if local_config_file.exists():
            with local_config_file.open() as f:
                local_config = json.load(f)
                uuid8 = local_config.get('uuid8', None)
                encrypted_secret = local_config.get('encrypted_secret', None)
                if encrypted_secret:
                    secret = fernet.decrypt(encrypted_secret.encode()).decode()
    return uuid8, secret


def dump_secret(work_path: 'Path', uuid8: str, secret: str):
    """Dump the UUID and Secret into local file

    :param work_path: the local package directory
    :param uuid8: the ID of the executor
    :param secret: the access secret
    """
    from cryptography.fernet import Fernet

    config = work_path / '.jina'
    config.mkdir(parents=True, exist_ok=True)

    local_id_file = config / 'secret.key'
    if local_id_file.exists():
        try:
            with local_id_file.open() as f:
                local_id, local_key = f.readline().strip().split('\t')
                fernet = Fernet(local_key.encode())
        except Exception:
            return
    else:
        local_id = str(random_identity())
        with local_id_file.open('w') as f:
            local_key = Fernet.generate_key()
            fernet = Fernet(local_key)
            f.write(f'{local_id}\t{local_key.decode()}')

    local_config_file = get_config_path(local_id)
    secret_data = {
        'uuid8': uuid8,
        'encrypted_secret': fernet.encrypt(secret.encode()).decode(),
    }
    with local_config_file.open('w') as f:
        f.write(json.dumps(secret_data))


def install_local(
    zip_package: 'Path',
    executor: 'HubExecutor',
    install_deps: Optional[bool] = False,
):
    """Install the package in zip format to the Jina Hub root.

    :param zip_package: the path of the zip file
    :param executor: the executor to install
    :param install_deps: if set, install dependencies
    """

    pkg_path, pkg_dist_path = get_dist_path(executor.uuid, executor.tag)

    # clean existed dist-info
    for dist in _hub_root.glob(f'{executor.uuid}-*.dist-info'):
        shutil.rmtree(dist)
    if pkg_path.exists():
        shutil.rmtree(pkg_path)

    try:
        # unpack the zip package to the root pkg_path
        unpack_package(zip_package, pkg_path)

        # create dist-info folder
        pkg_dist_path.mkdir(parents=False, exist_ok=True)

        # install the dependencies included in requirements.txt
        if install_deps:
            requirements_file = pkg_path / 'requirements.txt'
            if requirements_file.exists():
                install_requirements(requirements_file)
                shutil.copyfile(requirements_file, pkg_dist_path / 'requirements.txt')

        manifest_path = pkg_path / 'manifest.yml'
        if manifest_path.exists():
            shutil.copyfile(manifest_path, pkg_dist_path / 'manifest.yml')

        # store the serial number in local
        if executor.sn is not None:
            sn_file = pkg_dist_path / f'PKG-SN-{executor.sn}'
            sn_file.touch()

    except Exception as ex:
        # clean pkg_path, pkg_dist_path
        shutil.rmtree(pkg_path)
        shutil.rmtree(pkg_dist_path)
        raise ex


def uninstall_local(uuid: str):
    """Uninstall the executor package.

    :param uuid: the UUID of the executor
    """
    pkg_path, _ = get_dist_path(uuid, None)
    for dist in _hub_root.glob(f'{uuid}-*.dist-info'):
        shutil.rmtree(dist)
    if pkg_path.exists():
        shutil.rmtree(pkg_path)


def list_local():
    """List the locally-available executor packages.

    :return: the list of local executors (if found)
    """
    result = []
    for dist_name in _hub_root.glob(r'*-v*.dist-info'):
        result.append(dist_name)

    return result


def resolve_local(executor: 'HubExecutor') -> Optional['Path']:
    """Return the path of the executor if available.

    :param executor: the executor to check
    :return: the path of the executor package
    """
    pkg_path = _hub_root / executor.uuid
    pkg_dist_path = _hub_root / f'{executor.uuid}-{executor.tag}.dist-info'

    if not pkg_path.exists():
        raise FileNotFoundError(f'{pkg_path} does not exist')
    elif not pkg_dist_path.exists():
        raise FileNotFoundError(f'{pkg_dist_path} does not exist')
    else:
        return pkg_path, pkg_dist_path


def exist_local(uuid: str, tag: str = None) -> bool:
    """Check whether the executor exists in local

    :param uuid: the UUID of the executor
    :param tag: the TAG of the executor
    :return: True if existed, else False
    """
    try:
        resolve_local(HubExecutor(uuid=uuid, tag=tag))
        return True
    except FileNotFoundError:
        return False

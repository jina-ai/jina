"""Module wrapping interactions with the local executor packages."""

import json
import os
import shutil
from pathlib import Path
from typing import Tuple

from jina.hubble import HubExecutor
from jina.hubble.helper import (
    unpack_package,
    install_requirements,
    is_requirements_installed,
    get_hub_packages_dir,
)
from jina.helper import random_identity


def get_dist_path(uuid: str, tag: str) -> Tuple[Path, Path]:
    """Get the package path according ID and TAG
    :param uuid: the UUID of the executor
    :param tag: the TAG of the executor
    :return: package and its dist-info path
    """
    pkg_path = get_hub_packages_dir() / uuid
    pkg_dist_path = pkg_path / f'{tag}.dist-info'
    return pkg_path, pkg_dist_path


def get_dist_path_of_executor(executor: 'HubExecutor') -> Tuple[Path, Path]:
    """Return the path of the executor if available.

    :param executor: the executor to check
    :return: the path of the executor package
    """

    pkg_path, pkg_dist_path = get_dist_path(executor.uuid, executor.tag)

    if not pkg_path.exists():
        raise FileNotFoundError(f'{pkg_path} does not exist')
    elif not pkg_dist_path.exists():
        raise FileNotFoundError(f'{pkg_dist_path} does not exist')
    else:
        return pkg_path, pkg_dist_path


def get_config_path(local_id: str) -> 'Path':
    """Get the local configure file
    :param local_id: the random local ID of the executor
    :return: json config path
    """
    return get_hub_packages_dir() / f'{local_id}.json'


def get_lockfile() -> str:
    """Get the path of file locker
    :return: the path of file locker
    """
    return str(get_hub_packages_dir() / 'LOCK')


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
    install_deps: bool = False,
):
    """Install the package in zip format to the Jina Hub root.

    :param zip_package: the path of the zip file
    :param executor: the executor to install
    :param install_deps: if set, install dependencies
    """

    pkg_path, pkg_dist_path = get_dist_path(executor.uuid, executor.tag)

    # clean the existed dist_path
    for dist in pkg_path.glob(f'*.dist-info'):
        shutil.rmtree(dist)

    # unpack the zip package to the root pkg_path
    unpack_package(zip_package, pkg_path)

    # create dist-info folder
    pkg_dist_path.mkdir(parents=False, exist_ok=True)

    install_package_dependencies(install_deps, pkg_dist_path, pkg_path)

    manifest_path = pkg_path / 'manifest.yml'
    if manifest_path.exists():
        shutil.copyfile(manifest_path, pkg_dist_path / 'manifest.yml')

    # store the serial number in local
    if executor.sn is not None:
        sn_file = pkg_dist_path / f'PKG-SN-{executor.sn}'
        sn_file.touch()


def install_package_dependencies(
    install_deps: bool, pkg_dist_path: 'Path', pkg_path: 'Path'
) -> None:
    """

    :param install_deps: if set, then install dependencies
    :param pkg_dist_path: package distribution path
    :param pkg_path: package path
    """
    # install the dependencies included in requirements.txt
    requirements_file = pkg_path / 'requirements.txt'

    if requirements_file.exists():
        if pkg_path != pkg_dist_path:
            shutil.copyfile(requirements_file, pkg_dist_path / 'requirements.txt')

        if install_deps:
            install_requirements(requirements_file)
        elif not is_requirements_installed(requirements_file, show_warning=True):
            raise ModuleNotFoundError(
                'Dependencies listed in requirements.txt are not all installed locally, '
                'this Executor may not run as expect. To install dependencies, '
                'add `--install-requirements` or set `install_requirements = True`'
            )


def uninstall_local(uuid: str):
    """Uninstall the executor package.

    :param uuid: the UUID of the executor
    """
    pkg_path, _ = get_dist_path(uuid, None)
    for dist in get_hub_packages_dir().glob(f'{uuid}/*.dist-info'):
        shutil.rmtree(dist)
    if pkg_path.exists():
        shutil.rmtree(pkg_path)


def list_local():
    """List the locally-available executor packages.

    :return: the list of local executors (if found)
    """
    result = []
    for dist_name in get_hub_packages_dir().glob(r'*/v*.dist-info'):
        result.append(dist_name)

    return result


def exist_local(uuid: str, tag: str = None) -> bool:
    """Check whether the executor exists in local

    :param uuid: the UUID of the executor
    :param tag: the TAG of the executor
    :return: True if existed, else False
    """
    try:
        get_dist_path_of_executor(HubExecutor(uuid=uuid, tag=tag))
        return True
    except FileNotFoundError:
        return False

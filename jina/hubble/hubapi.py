"""Module wrapping interactions with the local executor packages."""


import os
import shutil
from pathlib import Path
from typing import Tuple

from .helper import unpack_package

from . import JINA_HUB_ROOT


def get_dist_path(id: str, tag: str) -> Tuple['Path', 'Path']:
    """Get the package path according ID and TAG
    :param id: the ID of the executor
    :param tag: the TAG of the executor
    :return: package and its dist-info path
    """
    pkg_path = JINA_HUB_ROOT / id
    pkg_dist_path = JINA_HUB_ROOT / f"{id}-{tag}.dist-info"
    return pkg_path, pkg_dist_path


def install_locall(zip_package: "Path", id: str, tag: str, force: bool = False):
    """Install the package in zip format to the Jina Hub root.

    :param zip_package: the path of the zip file
    :param id: the ID of the executor
    :param tag: the TAG of the executor
    :param force: if set, overwrites the package
    """

    pkg_path, pkg_dist_path = get_dist_path(id, tag)
    if pkg_dist_path.exists() and not force:
        return

    # clean existed dist-info
    for dist in JINA_HUB_ROOT.glob(f"{id}-*.dist-info"):
        shutil.rmtree(dist)

    # unpack the zip package to the root pkg_path
    unpack_package(zip_package, pkg_path)

    # TODO: install the dependencies included in requirements.txt

    # create dist-info folder
    pkg_dist_path.mkdir(parents=False, exist_ok=True)

    manifest_path = pkg_path / "manifest.yml"
    if manifest_path.exists():
        shutil.copyfile(manifest_path, pkg_dist_path / "manifest.yml")

    requirements_path = pkg_path / "requirements.txt"
    if requirements_path.exists():
        shutil.copyfile(requirements_path, pkg_dist_path / "requirements.txt")


def list_local():
    """List the locally-available executor packages.

    :return: the list of local executors (if found)
    """
    result = []
    for dist_name in JINA_HUB_ROOT.glob("*-*.dist-info"):
        result.append(dist_name)

    return dist_name


def resolve_local(id: str, tag: str = None) -> "Path":
    """Return the path of the executor if available.

    :param id: the ID of executor
    :param tag: the TAG of executor
    :return: the path of the executor package
    """
    pkg_path = JINA_HUB_ROOT / id
    pkg_dist_path = JINA_HUB_ROOT / f"{id}-{tag}.dist-info"
    if not pkg_path.exists():
        return None
    if tag and (not pkg_dist_path.exists()):
        return None
    return pkg_path


def exist_locall(id: str, tag: str = None) -> bool:
    """Check whether the executor exists in local

    :param id: the ID of the executor
    :param tag: the TAG of the executor
    :return: True if existed, else False
    """

    return resolve_local(id=id, tag=tag) is not None

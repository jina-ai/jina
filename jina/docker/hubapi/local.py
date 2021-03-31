"""Module wrapping interactions with the local images."""

import os
import pkgutil
from typing import Dict, Any, List, Optional

from pkg_resources import parse_version
from setuptools import find_packages

from ..helper import credentials_file
from ...excepts import HubLoginRequired
from ...helper import colored
from ...jaml import JAML
from ...logging import default_logger
from ... import __version__

_header_attrs = ['bold', 'underline']


def _load_local_hub_manifest():
    from ..checker import safe_url_name

    namespace = 'jina.hub'
    try:
        path = os.path.dirname(pkgutil.get_loader(namespace).path)
    except AttributeError:
        default_logger.warning(
            'local Hub is not initialized, '
            'try "git submodule update --init" if you are in dev mode'
        )
        return {}

    def _add_hub():
        m_yml = f'{info.module_finder.path}/manifest.yml'
        if info.ispkg and os.path.exists(m_yml):
            try:
                with open(m_yml) as fp:
                    m = JAML.load(fp)
                    m['source_path'] = info.module_finder.path
                    exec_name = safe_url_name(
                        f'jinahub/' + f'{m["type"]}.{m["kind"]}.{m["name"]}'
                    )
                    tag = exec_name + f':{m["version"]}-{__version__}'
                    m['image_tag'] = tag
                    hub_images[m['name']] = m
            except:
                pass  #: intentionally suppress the error, as some dirs do not fit to a valid hub structure

    hub_images = {}

    for info in pkgutil.iter_modules([path]):
        _add_hub()

    for pkg in find_packages(path):
        pkgpath = path + '/' + pkg.replace('.', '/')
        for info in pkgutil.iter_modules([pkgpath]):
            _add_hub()

    # filter
    return hub_images


def _list_local(logger) -> Optional[Dict[str, Any]]:
    """
    List the locally-available images.

    :param logger: the logger object with which to print
    :return: the list of manifests (if found)
    """
    manifests = _load_local_hub_manifest()
    if manifests:
        tb = _make_hub_table(manifests.values())
        logger.info('\n'.join(tb))
    return manifests


def _fetch_access_token(logger) -> Optional[str]:
    """
    Fetch github access token from credentials file, return as a request header

    :param logger: the logger object with which to print
    :return: local github access token (if found)
    """
    logger.info('fetching github access token...')

    if not credentials_file().is_file():
        raise HubLoginRequired(
            f'❌ User not logged in. please login using command: {colored("jina hub login", attrs=["bold"])}'
        )
    try:
        with open(credentials_file(), 'r') as cf:
            cred_yml = JAML.load(cf)
            access_token = cred_yml['access_token']
            return access_token
    except Exception:
        raise HubLoginRequired(
            f'❌ Invalid access file. '
            f'please re-login using command: {colored("jina hub login", attrs=["bold"])}'
        )


def _make_hub_table_with_local(images: Dict, local_images: Dict) -> List[str]:
    """
    Pretty print remote and local hub images

    :param images: remote images as a dict
    :param local_images: local images as a dict
    :return: table content to be pretty printed as a list
    """

    info_table = [
        f'found {len(images)} matched hub images',
        '{:<50s}{:<25s}{:<30s}{:<25s}{:<30s}{:<50s}'.format(
            colored('Name', attrs=_header_attrs),
            colored('Kind', attrs=_header_attrs),
            colored('Version', attrs=_header_attrs),
            colored('Local', attrs=_header_attrs),
            colored('Jina Version', attrs=_header_attrs),
            colored('Description', attrs=_header_attrs),
        ),
    ]
    images = sorted(images, key=lambda k: k['name'].lower())
    for image in images:
        image_name = image.get('name', '')
        kind = image.get('kind', '')
        ver = image.get('version', '')
        jina_ver = image.get('jina-version', '')
        desc = image.get('description', '')[:60].strip() + '...'
        if image_name and ver and desc:
            local_ver = ''
            color = 'white'
            if image_name in local_images:
                local_ver = local_images[image_name].get('version', '')
                _v1, _v2 = parse_version(ver), parse_version(local_ver)
                if _v1 > _v2:
                    color = 'red'
                elif _v1 == _v2:
                    color = 'green'
                else:
                    color = 'yellow'
            info_table.append(
                f'{colored(image_name, color="yellow", attrs="bold"):<50s}'
                f'{colored(kind, color="yellow"):<25s}'
                f'{colored(ver, color="green"):<25s}'
                f'{colored(local_ver, color=color):<25s}'
                f'{colored(jina_ver, color="green"):<25s}'
                f'{desc:<30s}'
            )
    return info_table


def _make_hub_table(images) -> List[str]:
    """
    Pretty print local hub images

    :param images: local images as a dict
    :return: table content to be pretty printed as a list
    """
    info_table = [
        f'found {len(images)} matched hub images',
        '{:<50s}{:<25s}{:<25s}{:<30s}'.format(
            colored('Name', attrs=_header_attrs),
            colored('Kind', attrs=_header_attrs),
            colored('Version', attrs=_header_attrs),
            colored('Description', attrs=_header_attrs),
        ),
    ]
    images = sorted(images, key=lambda k: k['name'].lower())
    for image in images:
        image_name = image.get('name', '')
        kind = image.get('kind', '')
        ver = image.get('version', '')
        desc = image.get('description', '')[:60].strip() + '...'
        if image_name and ver and desc:
            info_table.append(
                f'{colored(image_name, color="yellow", attrs="bold"):<50s}'
                f'{colored(kind, color="yellow"):<25s}'
                f'{colored(ver, color="green"):<25s}'
                f'{desc:<30s}'
            )
    return info_table

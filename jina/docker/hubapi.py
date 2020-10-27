import json
import os
import pkgutil
from pkgutil import iter_modules
from typing import Dict, Sequence, Any, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pkg_resources import resource_stream, parse_version
from setuptools import find_packages

from .helper import credentials_file
from ..helper import colored, yaml
from ..logging import default_logger
from ..logging.profile import TimeContext

_header_attrs = ['bold', 'underline']


def _load_local_hub_manifest():
    namespace = 'jina.hub'
    try:
        path = os.path.dirname(pkgutil.get_loader(namespace).path)
    except AttributeError:
        default_logger.warning('local Hub is not initialized, '
                               'try "git submodule update --init" if you are in dev mode')
        return {}

    def add_hub():
        m_yml = f'{info.module_finder.path}/manifest.yml'
        if info.ispkg and os.path.exists(m_yml):
            try:
                with open(m_yml) as fp:
                    m = yaml.load(fp)
                    hub_images[m['name']] = m
            except:
                pass

    hub_images = {}

    for info in iter_modules([path]):
        add_hub()

    for pkg in find_packages(path):
        pkgpath = path + '/' + pkg.replace('.', '/')
        for info in iter_modules([pkgpath]):
            add_hub()

    # filter
    return hub_images


def _list_local(logger) -> Optional[Dict[str, Any]]:
    """
    List all local hub manifests

    .. note:

        This does not implement query langauge

    """
    manifests = _load_local_hub_manifest()
    if manifests:
        tb = _make_hub_table(manifests.values())
        logger.info('\n'.join(tb))
    return manifests


def _list(logger, image_name: str = None, image_kind: str = None,
          image_type: str = None, image_keywords: Sequence = ()) -> Optional[Dict[str, Any]]:
    """ Use Hub api to get the list of filtered images

    :param logger: logger to use
    :param image_name:
    :param image_kind:
    :param image_type:
    :param image_keywords:
    :return: a dict of manifest specifications, each coresponds to a hub image
    """
    # TODO: Shouldn't pass a default argument for keywords. Need to handle after lambda function gets fixed
    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = yaml.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['list']

    params = {
        'name': image_name,
        'kind': image_kind,
        'type': image_type,
        'keywords': ','.join(image_keywords) if image_keywords else None
    }
    params = {k: v for k, v in params.items() if v}
    if params:
        data = urlencode(params)
        request = Request(f'{hubapi_url}?{data}')
        with TimeContext('searching', logger):
            try:
                with urlopen(request) as resp:
                    response = json.load(resp)
            except HTTPError as err:
                if err.code == 400:
                    logger.warning('no matched executors found. please use different filters and retry.')
                elif err.code == 500:
                    logger.error(f'server is down: {err.reason}')
                else:
                    logger.error(f'unknown error: {err.reason}')
                return

        manifests = response['manifest']
        local_manifest = _load_local_hub_manifest()
        if local_manifest:
            tb = _make_hub_table_with_local(manifests, local_manifest)
        else:
            tb = _make_hub_table(manifests)
        logger.info('\n'.join(tb))
        return manifests


def _make_hub_table_with_local(manifests, local_manifests):
    info_table = [f'found {len(manifests)} matched hub images',
                  '{:<50s}{:<20s}{:<20s}{:<30s}'.format(colored('Name', attrs=_header_attrs),
                                                        colored('Version', attrs=_header_attrs),
                                                        colored('Local', attrs=_header_attrs),
                                                        colored('Description', attrs=_header_attrs))]
    for index, manifest in enumerate(manifests):
        image_name = manifest.get('name', '')
        ver = manifest.get('version', '')
        desc = manifest.get('description', '')[:60].strip() + '...'
        if image_name and ver and desc:
            local_ver = ''
            color = 'white'
            if image_name in local_manifests:
                local_ver = local_manifests[image_name].get('version', '')
                _v1, _v2 = parse_version(ver), parse_version(local_ver)
                if _v1 > _v2:
                    color = 'red'
                elif _v1 == _v2:
                    color = 'green'
                else:
                    color = 'yellow'
            info_table.append(f'{colored(image_name, color="yellow", attrs="bold"):<50s}'
                              f'{colored(ver, color="green"):<20s}'
                              f'{colored(local_ver, color=color):<20s}'
                              f'{desc:<30s}')
    return info_table


def _make_hub_table(manifests):
    info_table = [f'found {len(manifests)} matched hub images',
                  '{:<50s}{:<20s}{:<30s}'.format(colored('Name', attrs=_header_attrs),
                                                 colored('Version', attrs=_header_attrs),
                                                 colored('Description', attrs=_header_attrs))]
    for index, manifest in enumerate(manifests):
        image_name = manifest.get('name', '')
        ver = manifest.get('version', '')
        desc = manifest.get('description', '')[:60].strip() + '...'
        if image_name and ver and desc:
            info_table.append(f'{colored(image_name, color="yellow", attrs="bold"):<50s}'
                              f'{colored(ver, color="green"):<20s}'
                              f'{desc:<30s}')
    return info_table


def _register_to_mongodb(logger, summary: Dict = None):
    """ Hub API Invocation to run `hub push` """
    logger.info('registering image to Jina Hub database...')

    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = yaml.load(fp)

    hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['push']

    if not credentials_file().is_file():
        logger.error(f'user hasnot logged in. please login using command: {colored("jina hub login", attrs=["bold"])}')
        return

    with open(credentials_file(), 'r') as cf:
        cred_yml = yaml.load(cf)
    access_token = cred_yml['access_token']

    if not access_token:
        logger.error(f'user has not logged in. please login using command: {colored("jina hub login", attrs=["bold"])}')
        return

    headers = {
        'Accept': 'application/json',
        'authorizationToken': access_token
    }
    try:
        import requests
        response = requests.post(url=f'{hubapi_url}',
                                 headers=headers,
                                 data=json.dumps(summary))
        if response.status_code == requests.codes.ok:
            logger.info(response.text)
        elif response.status_code == requests.codes.unauthorized:
            logger.error(f'user is unauthorized to perform push operation. '
                         f'please login using command: {colored("jina hub login", attrs=["bold"])}')
        elif response.status_code == requests.codes.internal_server_error:
            if 'auth' in response.text.lower():
                logger.error(f'authentication issues!'
                             f'please login using command: {colored("jina hub login", attrs=["bold"])}')
            logger.error(f'got an error from the API: {response.text}')
    except Exception as exp:
        logger.error(f'got an exception while invoking hubapi for push {repr(exp)}')

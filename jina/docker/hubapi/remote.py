import json
import base64
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pkg_resources import resource_stream
from typing import Dict, Sequence, Any, Optional, List

from ...jaml import JAML
from ...helper import colored
from ...importer import ImportExtensions
from ...logging.profile import TimeContext
from .local import _fetch_access_token, _make_hub_table, _make_hub_table_with_local, _load_local_hub_manifest


def _list(logger, image_name: str = None, image_kind: str = None,
          image_type: str = None, image_keywords: Sequence = ()) -> Optional[List[Dict[str, Any]]]:
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
        hubapi_yml = JAML.load(fp)
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


def _fetch_docker_auth(logger) -> Optional[Dict[str, str]]:
    """ Use Hub api to get docker creds

    :return: a dict of specifying username and password
    """
    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = JAML.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['docker_auth']

    try:
        with ImportExtensions(required=True,
                              help_text='missing "requests" dependency, please do pip install "jina[http]"'):
            import requests
            headers = {
                'Accept': 'application/json',
                'authorizationToken': _fetch_access_token(logger)
            }
            response = requests.get(url=f'{hubapi_url}', headers=headers)
            if response.status_code == requests.codes.ok:
                json_response = json.loads(response.text)
                username = base64.b64decode(json_response['docker_username']).decode('ascii')
                password = base64.b64decode(json_response['docker_password']).decode('ascii')
                logger.debug(f'Successfully fetched docker creds for user')
                return username, password
            else:
                logger.error(f'failed to fetch docker credentials. status code {response.status_code}')
    except Exception as exp:
        logger.error(f'got an exception while fetching docker credentials {exp!r}')


def _register_to_mongodb(logger, summary: Dict = None):
    """ Hub API Invocation to run `hub push` """
    logger.info('registering image to Jina Hub database...')

    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = JAML.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['push']

    try:
        with ImportExtensions(required=True,
                              help_text='missing "requests" dependency, please do pip install "jina[http]"'):
            import requests
            headers = {
                'Accept': 'application/json',
                'authorizationToken': _fetch_access_token(logger)
            }
            response = requests.post(url=f'{hubapi_url}',
                                     headers=headers,
                                     data=json.dumps(summary))
            if response.status_code == requests.codes.ok:
                logger.info(response.text)
            elif response.status_code == requests.codes.unauthorized:
                logger.critical(f'user is unauthorized to perform push operation. '
                                f'please login using command: {colored("jina hub login", attrs=["bold"])}')
            elif response.status_code == requests.codes.internal_server_error:
                if 'auth' in response.text.lower():
                    logger.critical(f'authentication issues!'
                                    f'please login using command: {colored("jina hub login", attrs=["bold"])}')
                logger.critical(f'got an error from the API: {response.text}')
    except Exception as exp:
        logger.error(f'got an exception while invoking hubapi for push {exp!r}')

import json
from typing import Dict, Sequence, Any, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pkg_resources import resource_stream

from .helper import credentials_file
from ..helper import yaml, colored
from ..logging.profile import TimeContext


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
        attrs = ['bold', 'underline']
        info_table = [f'found {len(manifests)} matched hub images',
                      '{:<40s}{:<20s}{:<30s}'.format(colored('Name', attrs=attrs),
                                                     colored('Version', attrs=attrs),
                                                     colored('Description', attrs=attrs))]

        for index, manifest in enumerate(manifests):
            image_name = manifest.get('name', '')
            ver = manifest.get('version', '')
            desc = manifest.get('description', '')[:50] + '...'
            if image_name and ver and desc:
                info_table.append(f'{colored(image_name, color="yellow", attrs="bold"):<40s}'
                                  f'{colored(ver, color="green"):<20s}'
                                  f'{desc:<30s}')
        logger.info('\n'.join(info_table))
        return manifests


def _push(logger, summary: Dict = None):
    """ Hub API Invocation to run `hub push` """
    if not summary:
        logger.error(f'summary is empty. nothing to do')
        return

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
        logger.error(f'user hasnot logged in. please login using command: {colored("jina hub login", attrs=["bold"])}')
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
        return

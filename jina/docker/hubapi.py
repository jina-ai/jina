import json
from typing import Dict
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests
from pkg_resources import resource_stream

from .helper import credentials_file
from ..helper import yaml, colored


def _list(logger, name: str = None, kind: str = None, type_: str = None, keywords: tuple = ('numeric')):
    """ Hub API Invocation to run `hub list` """
    # TODO: Shouldn't pass a default argument for keywords. Need to handle after lambda function gets fixed
    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = yaml.load(fp)

    hubapi_url = hubapi_yml['hubapi']['url']
    hubapi_list = hubapi_yml['hubapi']['list']
    params = {}
    if name:
        params['name'] = name
    if kind:
        params['kind'] = kind
    if type_:
        params['type'] = type_
    if keywords:
        # The way lambda function handles params, we need to pass them comma separated rather than in an iterable 
        params['keywords'] = ','.join(keywords) if len(keywords) > 1 else keywords
    if params:
        data = urlencode(params).encode()
        print(f'{hubapi_url}{hubapi_list}')
        request = Request(f'{hubapi_url}{hubapi_list}', data)

        try:
            with urlopen(request) as resp:
                response = json.load(resp)
        except HTTPError as err:
            if err.code == 400:
                logger.error('Could not find any executors. Please change the filter and retry!')
            elif err.code == 500:
                logger.error(f'Got the following server error! {err.reason}')
            else:
                logger.error(f'Unknown error: {err.reason}')

            return

        manifests = response['manifest']
        for index, manifest in enumerate(manifests):
            print(f'\n{colored("☟ Executor #" + str(index + 1), "cyan", attrs=["bold"])}')
            if 'name' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Name", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["name"]}')
            if 'version' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Version", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["version"]}')
            if 'description' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Description", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["description"]}')
            if 'author' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Author", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["author"]}')
            if 'kind' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Kind", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["kind"]}')
            if 'type' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Type", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["type"]}')
            if 'keywords' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Keywords", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["keywords"]}')
            if 'documentation' in manifest:
                print(f'{colored("☞", "green")} '
                      f'{colored("Documentation", "grey", attrs=["bold"]):<30s}: '
                      f'{manifest["documentation"]}')

        return response


def _push(logger, summary: Dict = None):
    """ Hub API Invocation to run `hub push` """
    if not summary:
        logger.error(f'summary is empty.nothing to do')
        return

    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = yaml.load(fp)

    hubapi_url = hubapi_yml['hubapi']['url']
    hubapi_push = hubapi_yml['hubapi']['push']

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
        response = requests.post(url=f'{hubapi_url}{hubapi_push}',
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

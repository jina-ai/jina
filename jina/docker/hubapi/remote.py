"""Module wrapping interactions with the remote Jina Hub API"""
from jina.logging.logger import JinaLogger
import json
import base64
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pkg_resources import resource_stream
from typing import Dict, Sequence, Any, Optional, List, Tuple


from .local import (
    _fetch_access_token,
    _make_hub_table,
    _make_hub_table_with_local,
    _load_local_hub_manifest,
)
from ...jaml import JAML
from ...helper import colored
from ...importer import ImportExtensions
from ...logging.profile import TimeContext
from ...excepts import HubLoginRequired


def _list(
    logger: JinaLogger,
    image_name: Optional[str] = None,
    image_kind: Optional[str] = None,
    image_type: Optional[str] = None,
    image_keywords: Sequence = (),
) -> Optional[List[Dict[str, Any]]]:
    """Use Hub api to get the list of filtered images.

    :param logger: logger to use
    :param image_name: name of hub image
    :param image_kind: kind of hub image (indexer/encoder/segmenter/crafter/evaluator/ranker etc)
    :param image_type: type of hub image (pod/app)
    :param image_keywords: keywords added in the manifest yml
    :return: a dict of manifest specifications, each coresponds to a hub image
    """
    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = JAML.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['list']

    params = {
        'name': image_name,
        'kind': image_kind,
        'type': image_type,
        'keywords': image_keywords,
    }
    params = {k: v for k, v in params.items() if v}
    if params:
        data = urlencode(params, doseq=True)
        request = Request(f'{hubapi_url}?{data}')
        with TimeContext('searching', logger):
            try:
                with urlopen(request) as resp:
                    response = json.load(resp)
            except HTTPError as err:
                if err.code == 400:
                    logger.warning(
                        'no matched executors found. please use different filters and retry.'
                    )
                elif err.code == 500:
                    logger.error(f'server is down: {err.reason}')
                else:
                    logger.error(f'unknown error: {err.reason}')
                return

        local_manifest = _load_local_hub_manifest()
        if local_manifest:
            tb = _make_hub_table_with_local(response, local_manifest)
        else:
            tb = _make_hub_table(response)
        logger.info('\n'.join(tb))
        return response


def _fetch_docker_auth(logger: JinaLogger) -> Tuple[str, str]:
    """Use Hub api to get docker credentials.

    :param logger: the logger instance
    :return: a dict of specifying username and password
    """
    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = JAML.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['docker_auth']

    with ImportExtensions(
        required=True,
        help_text='Missing "requests" dependency, please do pip install "jina[http]"',
    ):
        import requests

    headers = {
        'Accept': 'application/json',
        'authorizationToken': _fetch_access_token(logger),
    }
    response = requests.get(url=f'{hubapi_url}', headers=headers)
    if response.status_code != requests.codes.ok:
        raise HubLoginRequired(
            f'❌ Failed to fetch docker credentials. status code {response.status_code}'
        )
    json_response = json.loads(response.text)
    username = base64.b64decode(json_response['docker_username']).decode('ascii')
    password = base64.b64decode(json_response['docker_password']).decode('ascii')
    logger.debug(f'✅ Successfully fetched docker creds for user')
    return username, password


def _register_to_mongodb(logger: JinaLogger, summary: Optional[Dict] = None):
    """Hub API Invocation to run `hub push`.

    :param logger: the logger instance
    :param summary: the summary dict object
    """
    # TODO(Deepankar): implement to jsonschema based validation for summary
    logger.info('registering image to Jina Hub database...')

    with resource_stream('jina', '/'.join(('resources', 'hubapi.yml'))) as fp:
        hubapi_yml = JAML.load(fp)
        hubapi_url = hubapi_yml['hubapi']['url'] + hubapi_yml['hubapi']['push']

    with ImportExtensions(
        required=True,
        help_text='Missing "requests" dependency, please do pip install "jina[http]"',
    ):
        import requests

    headers = {
        'Accept': 'application/json',
        'authorizationToken': _fetch_access_token(logger),
    }
    response = requests.post(
        url=f'{hubapi_url}', headers=headers, data=json.dumps(summary)
    )
    if response.status_code == requests.codes.ok:
        logger.success(f'✅ Successfully updated the database. {response.text}')
    else:
        raise HubLoginRequired(
            f'❌ Got an error from the API: {response.text.rstrip()}. '
            f'Please login using command: {colored("jina hub login", attrs=["bold"])}'
        )


import requests
from pkg_resources import resource_stream

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
        params['keywords'] = ','.join(keywords)
    
    if params:
        response = requests.get(url=f'{hubapi_url}{hubapi_list}',
                                params=params)
        if response.status_code == requests.codes.bad_request and response.text == 'No docs found':
            print(f'\n{colored("✗ Could not find any executors. Please change the arguments and retry!", "red")}\n')
            return response
        
        if response.status_code == requests.codes.internal_server_error:
            logger.warning(f'Got the following server error: {response.text}')
            print(f'\n{colored("✗ Could not find any executors. Something wrong with the server!", "red")}\n')
            return response
        
        manifests = response.json()['manifest']
        for index, manifest in enumerate(manifests):
            print(f'\n{colored("☟ Executor #" + str(index+1), "cyan", attrs=["bold"])}')
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


def _push():
    """ Hub API Invocation to run `hub push` """
    # TODO
    pass

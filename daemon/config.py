from pydantic import BaseSettings, validator

from jina import __version__

__prefix__ = 'v1'


class BaseConfig(BaseSettings):
    class Config:
        env_prefix = 'JINAD_'


class FastAPIConfig(BaseConfig):
    NAME: str = 'Jina Remote Manager'
    DESCRIPTION: str = 'REST API for managing Jina on Remote'
    VERSION: str = __version__
    PREFIX: str = '/' + __prefix__


class OpenAPITags(BaseConfig):
    API_TAGS: list = [{
        'name': 'Jina Remote Management',
        'description': 'API to invoke remote Flows/Pods/Peas',
        'externalDocs': {
            'description': 'Jina Remote Context Manager',
            'url': 'https://docs.jina.ai/',
        },
    }]
    FLOW_API_TAGS: list = [{
        'name': 'Remote Flow Manager',
        'description': 'API to invoke local/remote Flows',
        'externalDocs': {
            'description': 'Jina Flow Context Manager',
            'url': 'https://docs.jina.ai/chapters/flow/index.html',
        },
    }]
    POD_API_TAGS: list = [{
        'name': 'Remote Pod Manager',
        'description': 'API to invoke remote Pods (__should be used by Flow APIs only__)',
        'externalDocs': {
            'description': 'Jina 101',
            'url': 'https://docs.jina.ai/chapters/101/.sphinx.html',
        },
    }]
    PEA_API_TAGS: list = [{
        'name': 'Remote Pea Manager',
        'description': 'API to invoke remote Peas',
        'externalDocs': {
            'description': 'Jina 101',
            'url': 'https://docs.jina.ai/chapters/101/.sphinx.html',
        },
    }]
    LOG_API_TAGS: list = [{
        'name': 'logs',
        'description': 'Endpoint to get streaming logs from flows/pods',
    }]


class ServerConfig(BaseConfig):
    # TODO: check if HOST can be a ipaddress.IPv4Address
    HOST: str = '0.0.0.0'
    PORT: int = 8000


class JinaDConfig(BaseConfig):
    CONTEXT: str = 'all'

    @validator('CONTEXT')
    def validate_name(cls, value):
        if value.lower() not in ['all', 'flow', 'pod', 'pea']:
            raise ValueError('CONTEXT must be either all, flow or pod or pea')
        return value.lower()


class LogConfig(BaseConfig):
    # TODO: Read config from some file
    PATH: str = '/tmp/jina-log/%s/log.log'


jinad_config = JinaDConfig()
log_config = LogConfig()
fastapi_config = FastAPIConfig()
server_config = ServerConfig()
openapitags_config = OpenAPITags()

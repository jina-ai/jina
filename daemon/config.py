from pydantic import BaseSettings, validator

from jina import __version__


class BaseConfig(BaseSettings):
    class Config:
        env_prefix = 'JINAD_'


class FastAPIConfig(BaseConfig):
    NAME: str = 'JinaD (Daemon)'
    DESCRIPTION: str = 'The REST API of the daemon for managing distributed Jina'
    VERSION: str = __version__


class OpenAPITags(BaseConfig):
    API_TAGS: list = [{
        'name': 'Distributed Jina management',
        'description': 'API to invoke distributed Flows/Pods/Peas',
        'externalDocs': {
            'description': 'Jina Documentation',
            'url': 'https://docs.jina.ai/',
        },
    }]
    FLOW_API_TAGS: list = [{
        'name': 'Managing distributed Flow',
        'description': 'API to invoke distributed Flows',
        'externalDocs': {
            'description': 'Jina Flow Context Manager',
            'url': 'https://docs.jina.ai/chapters/flow/index.html',
        },
    }]
    POD_API_TAGS: list = [{
        'name': 'Managing distributed Pod',
        'description': 'API to invoke distributed Pods (__should be used by Flow APIs only__)',
        'externalDocs': {
            'description': 'Jina 101',
            'url': 'https://docs.jina.ai/chapters/101/.sphinx.html',
        },
    }]
    PEA_API_TAGS: list = [{
        'name': 'Managing distributed Pea',
        'description': 'API to invoke distributed Peas',
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

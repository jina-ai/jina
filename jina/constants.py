import os as _os
import sys as _sys
from pathlib import Path as _Path
import datetime as _datetime

__windows__ = _sys.platform == 'win32'
__uptime__ = _datetime.datetime.now().isoformat()

# update on MacOS 1. clean this tuple, 2. grep -rohEI --exclude-dir=jina/hub --exclude-dir=tests --include \*.py
# "\'JINA_.*?\'" jina  | sort -u | sed "s/$/,/g" 3. copy all lines EXCEPT the first (which is the grep command in the
# last line)
__jina_env__ = (
    'JINA_DEFAULT_HOST',
    'JINA_DEFAULT_TIMEOUT_CTRL',
    'JINA_DEPLOYMENT_NAME',
    'JINA_DISABLE_UVLOOP',
    'JINA_EARLY_STOP',
    'JINA_FULL_CLI',
    'JINA_GATEWAY_IMAGE',
    'JINA_GRPC_RECV_BYTES',
    'JINA_GRPC_SEND_BYTES',
    'JINA_HUB_NO_IMAGE_REBUILD',
    'JINA_LOG_CONFIG',
    'JINA_LOG_LEVEL',
    'JINA_LOG_NO_COLOR',
    'JINA_MP_START_METHOD',
    'JINA_OPTOUT_TELEMETRY',
    'JINA_RANDOM_PORT_MAX',
    'JINA_RANDOM_PORT_MIN',
    'JINA_LOCKS_ROOT',
    'JINA_OPTOUT_TELEMETRY',
    'JINA_K8S_ACCESS_MODES',
    'JINA_K8S_STORAGE_CLASS_NAME',
    'JINA_K8S_STORAGE_CAPACITY',
    'JINA_STREAMER_ARGS',
)

__default_host__ = _os.getenv(
    'JINA_DEFAULT_HOST', '127.0.0.1' if __windows__ else '0.0.0.0'
)
__docker_host__ = 'host.docker.internal'
__default_executor__ = 'BaseExecutor'
__default_gateway__ = 'BaseGateway'
__default_http_gateway__ = 'HTTPGateway'
__default_composite_gateway__ = 'CompositeGateway'
__default_websocket_gateway__ = 'WebSocketGateway'
__default_grpc_gateway__ = 'GRPCGateway'
__default_endpoint__ = '/default'
__dynamic_base_gateway_hubble__ = 'jinaai+docker://jina-ai/JinaGateway:latest'
__ready_msg__ = 'ready and listening'
__stop_msg__ = 'terminated'
__unset_msg__ = '(unset)'
__args_executor_func__ = {
    'docs',
    'parameters',
    'docs_matrix',
}
__args_executor_init__ = {'metas', 'requests', 'runtime_args'}
__resources_path__ = _os.path.join(
    _os.path.dirname(_sys.modules['jina'].__file__), 'resources'
)
__cache_path__ = f'{_os.path.expanduser("~")}/.cache/{__package__}'
if not _Path(__cache_path__).exists():
    _Path(__cache_path__).mkdir(parents=True, exist_ok=True)

_names_with_underscore = [
    '__version__',
    '__proto_version__',
    '__default_host__',
    '__ready_msg__',
    '__stop_msg__',
    '__jina_env__',
    '__uptime__',
    '__default_endpoint__',
    '__default_executor__',
    '__unset_msg__',
    '__windows__',
]

__all__ = [_s for _s in dir() if not _s.startswith('_')] + _names_with_underscore

RAFT_TO_EXECUTOR_PORT = 100

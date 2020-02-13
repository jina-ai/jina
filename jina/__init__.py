# do not change this line manually
# this is managed by git tag and updated on every release
__version__ = '0.0.1'

# do not change this line manually
# this is managed by shell/build-proto.sh and updated on every execution
__proto_version__ = '0.0.5'

from datetime import datetime

__uptime__ = datetime.now().strftime('%Y%m%d%H%M%S')

__jina_env__ = ('JINA_PROFILING',
                'JINA_WARN_UNNAMED',
                'JINA_VCS_VERSION',
                'JINA_CONTROL_PORT',
                'JINA_CONTRIB_MODULE',
                'JINA_IPC_SOCK_TMP',
                'JINA_LOG_FORMAT',
                'JINA_SOCKET_HWM',
                'JINA_ARRAY_QUANT')

from types import SimpleNamespace

__default_host__ = '0.0.0.0'

JINA_GLOBAL = SimpleNamespace()
JINA_GLOBAL.executors_imported = False

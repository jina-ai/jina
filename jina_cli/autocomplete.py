ac_table = {
    'commands': [
        '--help',
        '--version',
        '--version-full',
        'executor',
        'flow',
        'ping',
        'export',
        'new',
        'gateway',
        'auth',
        'hub',
        'cloud',
        'help',
        'pod',
        'deployment',
        'client',
    ],
    'completions': {
        'executor': [
            '--help',
            '--name',
            '--workspace',
            '--log-config',
            '--quiet',
            '--quiet-error',
            '--workspace-id',
            '--extra-search-paths',
            '--timeout-ctrl',
            '--k8s-namespace',
            '--polling',
            '--shards',
            '--replicas',
            '--native',
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--uses-dynamic-batching',
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--no-reduce',
            '--disable-reduce',
            '--allow-concurrent',
            '--grpc-server-options',
            '--raft-configuration',
            '--grpc-channel-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--force-network-mode',
            '--host',
            '--host-in',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--env-from-secret',
            '--image-pull-secrets',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--floating',
            '--replica-id',
            '--reload',
            '--install-requirements',
            '--port',
            '--ports',
            '--protocol',
            '--protocols',
            '--provider',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--stateful',
            '--peer-ports',
            '--force-update',
            '--force',
            '--prefer-platform',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--timeout-send',
        ],
        'flow': [
            '--help',
            '--name',
            '--workspace',
            '--log-config',
            '--quiet',
            '--quiet-error',
            '--workspace-id',
            '--suppress-root-logging',
            '--uses',
            '--reload',
            '--env',
            '--inspect',
        ],
        'ping': [
            '--help',
            'flow',
            'executor',
            'gateway',
            '--timeout',
            '--attempts',
            '--min-successful-attempts',
        ],
        'export flowchart': ['--help', '--vertical-layout'],
        'export kubernetes': ['--help', '--k8s-namespace'],
        'export docker-compose': ['--help', '--network_name'],
        'export schema': ['--help', '--yaml-path', '--json-path', '--schema-path'],
        'export': ['--help', 'flowchart', 'kubernetes', 'docker-compose', 'schema'],
        'new': ['--help', '--type'],
        'gateway': [
            '--help',
            '--name',
            '--workspace',
            '--log-config',
            '--quiet',
            '--quiet-error',
            '--workspace-id',
            '--extra-search-paths',
            '--timeout-ctrl',
            '--k8s-namespace',
            '--entrypoint',
            '--docker-kwargs',
            '--prefetch',
            '--title',
            '--description',
            '--cors',
            '--uvicorn-kwargs',
            '--ssl-certfile',
            '--ssl-keyfile',
            '--no-debug-endpoints',
            '--no-crud-endpoints',
            '--expose-endpoints',
            '--expose-graphql-endpoint',
            '--host',
            '--host-in',
            '--proxy',
            '--uses',
            '--uses-with',
            '--py-modules',
            '--replicas',
            '--grpc-server-options',
            '--grpc-channel-options',
            '--graph-description',
            '--graph-conditions',
            '--deployments-addresses',
            '--deployments-metadata',
            '--deployments-no-reduce',
            '--deployments-disable-reduce',
            '--compression',
            '--timeout-send',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--env-from-secret',
            '--image-pull-secrets',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--floating',
            '--replica-id',
            '--reload',
            '--port',
            '--ports',
            '--port-expose',
            '--port-in',
            '--protocol',
            '--protocols',
            '--provider',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--stateful',
            '--peer-ports',
        ],
        'auth login': ['--help', '--force'],
        'auth logout': ['--help'],
        'auth token create': ['--help', '--expire', '--format'],
        'auth token delete': ['--help'],
        'auth token list': ['--help'],
        'auth token': ['--help', 'create', 'delete', 'list'],
        'auth': ['--help', 'login', 'logout', 'token'],
        'hub new': [
            '--help',
            '--name',
            '--path',
            '--advance-configuration',
            '--description',
            '--keywords',
            '--url',
            '--dockerfile',
        ],
        'hub push': [
            '--help',
            '--no-usage',
            '--verbose',
            '--dockerfile',
            '--tag',
            '--protected-tag',
            '--force-update',
            '--force',
            '--build-env',
            '--platform',
            '--secret',
            '--no-cache',
            '--public',
            '--private',
        ],
        'hub pull': [
            '--help',
            '--no-usage',
            '--force-update',
            '--force',
            '--prefer-platform',
            '--install-requirements',
        ],
        'hub status': ['--help', '--id', '--verbose', '--replay'],
        'hub list': ['--help'],
        'hub': ['--help', 'new', 'push', 'pull', 'status', 'list'],
        'cloud login': ['--help'],
        'cloud logout': ['--help'],
        'cloud flow list': ['--help', '--phase', '--name', '--labels'],
        'cloud flow remove': ['--help', '--phase'],
        'cloud flow update': ['--help'],
        'cloud flow restart': ['--help', '--gateway', '--executor'],
        'cloud flow pause': ['--help'],
        'cloud flow resume': ['--help'],
        'cloud flow scale': ['--help', '--executor', '--replicas'],
        'cloud flow recreate': ['--help'],
        'cloud flow status': ['--help', '--verbose'],
        'cloud flow deploy': ['--help'],
        'cloud flow normalize': ['--help', '--output', '--verbose'],
        'cloud flow logs': ['--help', '--gateway', '--executor'],
        'cloud flow': [
            '--help',
            'list',
            'remove',
            'update',
            'restart',
            'pause',
            'resume',
            'scale',
            'recreate',
            'status',
            'deploy',
            'normalize',
            'logs',
        ],
        'cloud flows list': ['--help', '--phase', '--name', '--labels'],
        'cloud flows remove': ['--help', '--phase'],
        'cloud flows update': ['--help'],
        'cloud flows restart': ['--help', '--gateway', '--executor'],
        'cloud flows pause': ['--help'],
        'cloud flows resume': ['--help'],
        'cloud flows scale': ['--help', '--executor', '--replicas'],
        'cloud flows recreate': ['--help'],
        'cloud flows status': ['--help', '--verbose'],
        'cloud flows deploy': ['--help'],
        'cloud flows normalize': ['--help', '--output', '--verbose'],
        'cloud flows logs': ['--help', '--gateway', '--executor'],
        'cloud flows': [
            '--help',
            'list',
            'remove',
            'update',
            'restart',
            'pause',
            'resume',
            'scale',
            'recreate',
            'status',
            'deploy',
            'normalize',
            'logs',
        ],
        'cloud job list': ['--help'],
        'cloud job remove': ['--help'],
        'cloud job logs': ['--help'],
        'cloud job create': ['--help', '--timeout', '--backofflimit', '--secrets'],
        'cloud job get': ['--help'],
        'cloud job': ['--help', 'list', 'remove', 'logs', 'create', 'get'],
        'cloud jobs list': ['--help'],
        'cloud jobs remove': ['--help'],
        'cloud jobs logs': ['--help'],
        'cloud jobs create': ['--help', '--timeout', '--backofflimit', '--secrets'],
        'cloud jobs get': ['--help'],
        'cloud jobs': ['--help', 'list', 'remove', 'logs', 'create', 'get'],
        'cloud secret list': ['--help'],
        'cloud secret remove': ['--help'],
        'cloud secret update': ['--help', '--from-literal', '--update', '--path'],
        'cloud secret create': ['--help', '--from-literal', '--update', '--path'],
        'cloud secret get': ['--help'],
        'cloud secret': ['--help', 'list', 'remove', 'update', 'create', 'get'],
        'cloud secrets list': ['--help'],
        'cloud secrets remove': ['--help'],
        'cloud secrets update': ['--help', '--from-literal', '--update', '--path'],
        'cloud secrets create': ['--help', '--from-literal', '--update', '--path'],
        'cloud secrets get': ['--help'],
        'cloud secrets': ['--help', 'list', 'remove', 'update', 'create', 'get'],
        'cloud new': ['--help'],
        'cloud': [
            '--help',
            '--version',
            '--loglevel',
            'login',
            'logout',
            'flow',
            'flows',
            'job',
            'jobs',
            'secret',
            'secrets',
            'new',
        ],
        'help': ['--help'],
        'pod': [
            '--help',
            '--name',
            '--workspace',
            '--log-config',
            '--quiet',
            '--quiet-error',
            '--workspace-id',
            '--extra-search-paths',
            '--timeout-ctrl',
            '--k8s-namespace',
            '--polling',
            '--shards',
            '--replicas',
            '--native',
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--uses-dynamic-batching',
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--no-reduce',
            '--disable-reduce',
            '--allow-concurrent',
            '--grpc-server-options',
            '--raft-configuration',
            '--grpc-channel-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--force-network-mode',
            '--host',
            '--host-in',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--env-from-secret',
            '--image-pull-secrets',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--floating',
            '--replica-id',
            '--reload',
            '--install-requirements',
            '--port',
            '--ports',
            '--protocol',
            '--protocols',
            '--provider',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--stateful',
            '--peer-ports',
            '--force-update',
            '--force',
            '--prefer-platform',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--timeout-send',
        ],
        'deployment': [
            '--help',
            '--name',
            '--workspace',
            '--log-config',
            '--quiet',
            '--quiet-error',
            '--workspace-id',
            '--extra-search-paths',
            '--timeout-ctrl',
            '--k8s-namespace',
            '--polling',
            '--shards',
            '--replicas',
            '--native',
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--uses-dynamic-batching',
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--no-reduce',
            '--disable-reduce',
            '--allow-concurrent',
            '--grpc-server-options',
            '--raft-configuration',
            '--grpc-channel-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--force-network-mode',
            '--host',
            '--host-in',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--env-from-secret',
            '--image-pull-secrets',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--floating',
            '--replica-id',
            '--reload',
            '--install-requirements',
            '--port',
            '--ports',
            '--protocol',
            '--protocols',
            '--provider',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--stateful',
            '--peer-ports',
            '--force-update',
            '--force',
            '--prefer-platform',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--timeout-send',
            '--uses-before',
            '--uses-after',
            '--when',
            '--external',
            '--grpc-metadata',
            '--deployment-role',
            '--tls',
            '--title',
            '--description',
            '--cors',
            '--uvicorn-kwargs',
            '--ssl-certfile',
            '--ssl-keyfile',
        ],
        'client': [
            '--help',
            '--proxy',
            '--host',
            '--host-in',
            '--port',
            '--tls',
            '--asyncio',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--log-config',
            '--protocol',
            '--grpc-channel-options',
            '--prefetch',
            '--suppress-root-logging',
        ],
    },
}

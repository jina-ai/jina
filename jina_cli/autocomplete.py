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
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--disable-reduce',
            '--docs-by-executor',
            '--port-in',
            '--host-in',
            '--grpc-server-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--host',
            '--quiet-remote-logs',
            '--upload-files',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--install-requirements',
            '--force-update',
            '--force',
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
            '--uses',
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
        'new': ['--help'],
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
            '--no-debug-endpoints',
            '--no-crud-endpoints',
            '--expose-endpoints',
            '--uvicorn-kwargs',
            '--ssl-certfile',
            '--ssl-keyfile',
            '--expose-graphql-endpoint',
            '--protocol',
            '--host',
            '--proxy',
            '--uses',
            '--uses-with',
            '--py-modules',
            '--port-in',
            '--host-in',
            '--grpc-server-options',
            '--port-expose',
            '--graph-description',
            '--graph-conditions',
            '--deployments-addresses',
            '--deployments-metadata',
            '--deployments-disable-reduce',
            '--compression',
            '--timeout-send',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
        ],
        'auth login': ['--help', '--force'],
        'auth logout': ['--help'],
        'auth token create': ['--help', '--expire'],
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
            '--secret',
            '--no-cache',
            '--public',
            '--private',
        ],
        'hub pull': [
            '--help',
            '--no-usage',
            '--install-requirements',
            '--force-update',
            '--force',
        ],
        'hub status': ['--help', '--id', '--verbose', '--replay'],
        'hub list': ['--help'],
        'hub': ['--help', 'new', 'push', 'pull', 'status', 'list'],
        'cloud login': ['--help'],
        'cloud logout': ['--help'],
        'cloud deploy': ['--help', '--name', '--workspace', '--env-file'],
        'cloud list': ['--help', '--status'],
        'cloud logs': ['--help', '--executor'],
        'cloud status': ['--help'],
        'cloud remove': ['--help'],
        'cloud new': ['--help'],
        'cloud survey': ['--help'],
        'cloud': [
            '--help',
            '--version',
            '--loglevel',
            'login',
            'logout',
            'deploy',
            'list',
            'logs',
            'status',
            'remove',
            'new',
            'survey',
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
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--disable-reduce',
            '--docs-by-executor',
            '--port-in',
            '--host-in',
            '--grpc-server-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--host',
            '--quiet-remote-logs',
            '--upload-files',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--install-requirements',
            '--force-update',
            '--force',
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
            '--py-modules',
            '--output-array-type',
            '--exit-on-exceptions',
            '--disable-reduce',
            '--docs-by-executor',
            '--port-in',
            '--host-in',
            '--grpc-server-options',
            '--entrypoint',
            '--docker-kwargs',
            '--volumes',
            '--gpus',
            '--disable-auto-volume',
            '--host',
            '--quiet-remote-logs',
            '--upload-files',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--install-requirements',
            '--force-update',
            '--force',
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
        ],
        'client': [
            '--help',
            '--host',
            '--proxy',
            '--port',
            '--tls',
            '--asyncio',
            '--tracing',
            '--traces-exporter-host',
            '--traces-exporter-port',
            '--metrics',
            '--metrics-exporter-host',
            '--metrics-exporter-port',
            '--protocol',
        ],
    },
}

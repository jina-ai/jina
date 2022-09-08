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
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--py-modules',
            '--port-in',
            '--host-in',
            '--native',
            '--output-array-type',
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
            '--shards',
            '--replicas',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--install-requirements',
            '--force-update',
            '--force',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--disable-reduce',
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
        'ping': ['--help', 'flow', 'executor', '--timeout', '--retries'],
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
            '--polling',
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--py-modules',
            '--port-in',
            '--host-in',
            '--native',
            '--output-array-type',
            '--grpc-server-options',
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
            '--port-expose',
            '--graph-description',
            '--graph-conditions',
            '--deployments-addresses',
            '--deployments-disable-reduce',
            '--compression',
            '--timeout-send',
            '--runtime-cls',
            '--timeout-ready',
            '--env',
            '--shard-id',
            '--pod-role',
            '--noblock-on-start',
            '--shards',
            '--replicas',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
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
        'hub': ['--help', 'new', 'push', 'pull'],
        'cloud login': ['--help'],
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
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--py-modules',
            '--port-in',
            '--host-in',
            '--native',
            '--output-array-type',
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
            '--shards',
            '--replicas',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--install-requirements',
            '--force-update',
            '--force',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--disable-reduce',
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
            '--uses',
            '--uses-with',
            '--uses-metas',
            '--uses-requests',
            '--py-modules',
            '--port-in',
            '--host-in',
            '--native',
            '--output-array-type',
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
            '--shards',
            '--replicas',
            '--port',
            '--monitoring',
            '--port-monitoring',
            '--retries',
            '--floating',
            '--install-requirements',
            '--force-update',
            '--force',
            '--compression',
            '--uses-before-address',
            '--uses-after-address',
            '--connection-list',
            '--disable-reduce',
            '--timeout-send',
            '--uses-before',
            '--uses-after',
            '--when',
            '--external',
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
            '--protocol',
        ],
    },
}

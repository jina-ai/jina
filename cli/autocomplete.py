__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def _update_autocomplete():
    from jina.parser import get_main_parser

    def _gaa(key, parser):
        _result = {}
        _compl = []
        for v in parser._actions:
            if v.option_strings:
                _compl.extend(v.option_strings)
            elif v.choices:
                _compl.extend(v.choices)
                for kk, vv in v.choices.items():
                    _result.update(_gaa(' '.join([key, kk]).strip(), vv))
        # filer out single dash, as they serve as abbrev
        _compl = [k for k in _compl if (not k.startswith('-') or k.startswith('--'))]
        _result.update({key: _compl})
        return _result

    compl = _gaa('', get_main_parser())
    cmd = compl.pop('')
    compl = {'commands': cmd, 'completions': compl}

    with open(__file__, 'a') as fp:
        fp.write(f'\nac_table = {compl}\n')


if __name__ == '__main__':
    _update_autocomplete()

ac_table = {
    'commands': ['--help', '--version', '--version-full', 'hello-world', 'pod', 'flow', 'gateway', 'ping', 'check',
                 'hub', 'pea', 'log', 'client', 'export-api'], 'completions': {
        'hello-world': ['--help', '--workdir', '--logserver', '--logserver-config', '--download-proxy', '--shards',
                        '--parallel', '--uses-index', '--index-data-url', '--index-batch-size', '--uses-query',
                        '--query-data-url', '--query-batch-size', '--num-query', '--top-k'],
        'pod': ['--help', '--name', '--identity', '--uses', '--py-modules', '--uses-internal', '--entrypoint',
                '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--pea-id', '--num-part',
                '--role', '--skip-on-error', '--memory-hwm', '--runtime', '--max-idle-time', '--daemon', '--log-config',
                '--log-remote', '--log-id', '--ssh-server', '--ssh-keyfile', '--ssh-password', '--host',
                '--port-expose', '--port-grpc', '--max-message-size', '--proxy', '--remote-access', '--parallel',
                '--shards', '--polling', '--scheduling', '--uses-before', '--uses-after', '--shutdown-idle'],
        'flow': ['--help', '--uses', '--logserver', '--logserver-config', '--log-id', '--optimize-level',
                 '--output-type', '--output-path', '--inspect'],
        'gateway': ['--help', '--name', '--identity', '--uses', '--py-modules', '--uses-internal', '--entrypoint',
                    '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                    '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                    '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--pea-id',
                    '--num-part', '--role', '--skip-on-error', '--memory-hwm', '--runtime', '--max-idle-time',
                    '--daemon', '--log-config', '--log-remote', '--log-id', '--ssh-server', '--ssh-keyfile',
                    '--ssh-password', '--host', '--port-expose', '--port-grpc', '--max-message-size', '--proxy',
                    '--remote-access', '--prefetch', '--prefetch-on-recv', '--rest-api', '--check-version',
                    '--compress', '--compress-hwm', '--compress-lwm'],
        'ping': ['--help', '--timeout', '--retries', '--print-response'],
        'check': ['--help', '--summary-exec', '--summary-driver'], 'hub login': ['--help'],
        'hub new': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub init': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub create': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub build': ['--help', '--username', '--password', '--registry', '--repository', '--pull', '--push',
                      '--dry-run', '--prune-images', '--raise-error', '--test-uses', '--test-level', '--host-info',
                      '--daemon'], 'hub push': ['--help', '--username', '--password', '--registry', '--repository'],
        'hub pull': ['--help', '--username', '--password', '--registry', '--repository'],
        'hub list': ['--help', '--name', '--kind', '--keywords', '--type', '--local-only'],
        'hub': ['--help', 'login', 'new', 'init', 'create', 'build', 'push', 'pull', 'list'],
        'pea': ['--help', '--name', '--identity', '--uses', '--py-modules', '--uses-internal', '--entrypoint',
                '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--pea-id', '--num-part',
                '--role', '--skip-on-error', '--memory-hwm', '--runtime', '--max-idle-time', '--daemon', '--log-config',
                '--log-remote', '--log-id', '--ssh-server', '--ssh-keyfile', '--ssh-password', '--host',
                '--port-expose', '--port-grpc', '--max-message-size', '--proxy', '--remote-access'],
        'log': ['--help', '--groupby-regex', '--refresh-time'],
        'client': ['--help', '--host', '--port-expose', '--port-grpc', '--max-message-size', '--proxy',
                   '--remote-access', '--batch-size', '--mode', '--top-k', '--mime-type', '--callback-on',
                   '--timeout-ready', '--skip-dry-run', '--continue-on-error'],
        'export-api': ['--help', '--yaml-path', '--json-path']}}

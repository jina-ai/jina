__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def _update_autocomplete():
    from jina.main.parser import get_main_parser

    def _gaa(parser):
        _compl = []
        for v in parser._actions:
            if v.option_strings:
                _compl.extend(v.option_strings)
            elif v.choices:
                _compl.extend(v.choices)
        # filer out single dash, as they serve as abbrev
        _compl = [k for k in _compl if (not k.startswith('-') or k.startswith('--'))]
        return _compl

    compl = {
        'commands': _gaa(get_main_parser()),
        'completions': {k: _gaa(v) for k, v in get_main_parser()._actions[-1].choices.items()}
    }

    with open(__file__, 'a') as fp:
        fp.write(f'\nac_table = {compl}\n')


if __name__ == '__main__':
    _update_autocomplete()

ac_table = {
    'commands': ['--help', '--version', '--version-full', 'hello-world', 'pod', 'flow', 'gateway', 'ping', 'check',
                 'pea', 'log', 'client', 'export-api'], 'completions': {
        'hello-world': ['--help', '--workdir', '--logserver', '--shards', '--replicas', '--index-yaml-path',
                        '--index-data-url', '--index-batch-size', '--query-yaml-path', '--query-data-url',
                        '--query-batch-size', '--num-query', '--top-k'],
        'pod': ['--help', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint',
                '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id',
                '--check-version', '--array-in-pb', '--compress-hwm', '--compress-lwm', '--num-part', '--role',
                '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile',
                '--log-with-own-name', '--host', '--port-grpc', '--max-message-size', '--proxy', '--replicas',
                '--polling', '--scheduling', '--reducing-yaml-path', '--shutdown-idle'],
        'flow': ['--help', '--yaml-path', '--logserver', '--logserver-config', '--optimize-level', '--output-type',
                 '--output-path'],
        'gateway': ['--help', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint',
                    '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                    '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                    '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id',
                    '--check-version', '--array-in-pb', '--compress-hwm', '--compress-lwm', '--num-part', '--role',
                    '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile',
                    '--log-with-own-name', '--host', '--port-grpc', '--max-message-size', '--proxy', '--prefetch',
                    '--prefetch-on-recv', '--allow-spawn', '--rest-api'],
        'ping': ['--help', '--timeout', '--retries', '--print-response'],
        'check': ['--help', '--summary-exec', '--summary-driver'],
        'pea': ['--help', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint',
                '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in',
                '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready',
                '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id',
                '--check-version', '--array-in-pb', '--compress-hwm', '--compress-lwm', '--num-part', '--role',
                '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile',
                '--log-with-own-name', '--host', '--port-grpc', '--max-message-size', '--proxy'],
        'log': ['--help', '--groupby-regex', '--refresh-time'],
        'client': ['--help', '--host', '--port-grpc', '--max-message-size', '--proxy', '--batch-size', '--mode',
                   '--top-k', '--mime-type', '--callback-on-body', '--first-request-id', '--first-doc-id',
                   '--random-doc-id', '--timeout-ready'], 'export-api': ['--help', '--yaml-path', '--json-path']}}

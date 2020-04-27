__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

def _update_autocomplete():
    from jina.main.parser import get_main_parser, set_pea_parser, \
        set_hw_parser, set_flow_parser, set_pod_parser, \
        set_check_parser, set_gateway_parser, set_ping_parser, set_client_cli_parser, set_logger_parser

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
        'completions': {
            'pea': _gaa(set_pea_parser()),
            'hello-world': _gaa(set_hw_parser()),
            'flow': _gaa(set_flow_parser()),
            'pod': _gaa(set_pod_parser()),
            'check': _gaa(set_check_parser()),
            'gateway': _gaa(set_gateway_parser()),
            'ping': _gaa(set_ping_parser()),
            'client': _gaa(set_client_cli_parser()),
            'log': _gaa(set_logger_parser())
        }
    }

    with open(__file__, 'a') as fp:
        fp.write(f'\nac_table = {compl}\n')


if __name__ == '__main__':
    _update_autocomplete()

ac_table = {'commands': ['--help', '--version', '--version-full', 'hello-world', 'pod', 'flow', 'gateway', 'ping', 'check', 'pea', 'log', 'client'], 'completions': {'pea': ['--help', '--version', '--version-full', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint', '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready', '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id', '--check-version', '--array-in-pb', '--num-part', '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile', '--override-exec-log', '--host', '--port-grpc', '--max-message-size', '--proxy'], 'hello-world': ['--help', '--version', '--version-full', '--workdir', '--logserver', '--shards', '--replicas', '--index-yaml-path', '--index-data-url', '--index-batch-size', '--query-yaml-path', '--query-data-url', '--query-batch-size', '--num-query', '--top-k'], 'flow': ['--help', '--version', '--version-full', '--yaml-path', '--logserver', '--logserver-config', '--optimize-level', '--output-type', '--output-path'], 'pod': ['--help', '--version', '--version-full', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint', '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready', '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id', '--check-version', '--array-in-pb', '--num-part', '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile', '--override-exec-log', '--host', '--port-grpc', '--max-message-size', '--proxy', '--replicas', '--polling', '--scheduling', '--reducing-yaml-path', '--shutdown-idle'], 'check': ['--help', '--version', '--version-full', '--summary-exec', '--summary-driver'], 'gateway': ['--help', '--version', '--version-full', '--name', '--identity', '--yaml-path', '--py-modules', '--image', '--entrypoint', '--pull-latest', '--volumes', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out', '--port-ctrl', '--ctrl-with-ipc', '--timeout', '--timeout-ctrl', '--timeout-ready', '--dump-interval', '--exit-no-dump', '--read-only', '--separated-workspace', '--replica-id', '--check-version', '--array-in-pb', '--num-part', '--memory-hwm', '--runtime', '--max-idle-time', '--log-sse', '--log-remote', '--log-profile', '--override-exec-log', '--host', '--port-grpc', '--max-message-size', '--proxy', '--prefetch', '--prefetch-on-recv', '--allow-spawn'], 'ping': ['--help', '--version', '--version-full', '--timeout', '--retries', '--print-response'], 'client': ['--help', '--version', '--version-full', '--host', '--port-grpc', '--max-message-size', '--proxy', '--batch-size', '--mode', '--top-k', '--in-proto', '--callback-on-body', '--first-request-id', '--first-doc-id', '--random-doc-id', '--timeout-ready'], 'log': ['--help', '--version', '--version-full', '--groupby-regex', '--refresh-time']}}

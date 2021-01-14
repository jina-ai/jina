__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


def _update_autocomplete():
    from jina.parsers import get_main_parser

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
        'hello-world': ['--help', '--workdir', '--download-proxy', '--shards', '--parallel', '--uses-index',
                        '--index-data-url', '--index-labels-url', '--index-request-size', '--uses-query',
                        '--query-data-url', '--query-labels-url', '--query-request-size', '--num-query', '--top-k'],
        'pod': ['--help', '--name', '--log-config', '--identity', '--log-id', '--show-exc-info', '--port-ctrl',
                '--ctrl-with-ipc', '--timeout-ctrl', '--ssh-server', '--ssh-keyfile', '--ssh-password', '--uses',
                '--py-modules', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out',
                '--max-socket-retries', '--dump-interval', '--read-only', '--separated-workspace', '--memory-hwm',
                '--skip-on-error', '--num-part', '--uses-internal', '--entrypoint', '--pull-latest', '--volumes',
                '--host', '--port-expose', '--daemon', '--runtime-backend', '--runtime', '--runtime-cls',
                '--timeout-ready', '--env', '--expose-public', '--pea-id', '--pea-role', '--uses-before',
                '--uses-after', '--parallel', '--shards', '--polling', '--scheduling', '--remote-access',
                '--remote-type', '--pod-role'],
        'flow': ['--help', '--uses', '--log-id', '--optimize-level', '--output-type', '--output-path', '--inspect'],
        'gateway': ['--help', '--name', '--log-config', '--identity', '--log-id', '--show-exc-info', '--port-ctrl',
                    '--ctrl-with-ipc', '--timeout-ctrl', '--ssh-server', '--ssh-keyfile', '--ssh-password', '--uses',
                    '--py-modules', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out',
                    '--max-socket-retries', '--dump-interval', '--read-only', '--separated-workspace', '--memory-hwm',
                    '--skip-on-error', '--num-part', '--max-message-size', '--proxy', '--prefetch',
                    '--prefetch-on-recv', '--restful', '--rest-api', '--host', '--port-expose', '--daemon',
                    '--runtime-backend', '--runtime', '--runtime-cls', '--timeout-ready', '--env', '--expose-public',
                    '--pea-id', '--pea-role'], 'ping': ['--help', '--timeout', '--retries', '--print-response'],
        'check': ['--help', '--summary-exec', '--summary-driver'],
        'hub login': ['--help', '--username', '--password', '--registry', '--repository'],
        'hub new': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub init': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub create': ['--help', '--output-dir', '--template', '--type', '--overwrite'],
        'hub build': ['--help', '--username', '--password', '--registry', '--repository', '--pull', '--push',
                      '--dry-run', '--prune-images', '--raise-error', '--test-uses', '--test-level', '--timeout-ready',
                      '--host-info', '--daemon', '--no-overwrite'],
        'hub push': ['--help', '--username', '--password', '--registry', '--repository', '--no-overwrite'],
        'hub pull': ['--help', '--username', '--password', '--registry', '--repository', '--no-overwrite'],
        'hub list': ['--help', '--username', '--password', '--registry', '--repository', '--name', '--kind',
                     '--keywords', '--type', '--local-only'],
        'hub': ['--help', 'login', 'new', 'init', 'create', 'build', 'push', 'pull', 'list'],
        'pea': ['--help', '--name', '--log-config', '--identity', '--log-id', '--show-exc-info', '--port-ctrl',
                '--ctrl-with-ipc', '--timeout-ctrl', '--ssh-server', '--ssh-keyfile', '--ssh-password', '--uses',
                '--py-modules', '--port-in', '--port-out', '--host-in', '--host-out', '--socket-in', '--socket-out',
                '--max-socket-retries', '--dump-interval', '--read-only', '--separated-workspace', '--memory-hwm',
                '--skip-on-error', '--num-part', '--uses-internal', '--entrypoint', '--pull-latest', '--volumes',
                '--host', '--port-expose', '--daemon', '--runtime-backend', '--runtime', '--runtime-cls',
                '--timeout-ready', '--env', '--expose-public', '--pea-id', '--pea-role'],
        'log': ['--help', '--groupby-regex', '--refresh-time'],
        'client': ['--help', '--request-size', '--mode', '--top-k', '--mime-type', '--continue-on-error',
                   '--return-results', '--max-message-size', '--proxy', '--prefetch', '--prefetch-on-recv', '--restful',
                   '--rest-api', '--host', '--port-expose'], 'export-api': ['--help', '--yaml-path', '--json-path']}}

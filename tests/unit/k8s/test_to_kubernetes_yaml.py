import yaml

from jina import Flow
from jina.serve.networking import GrpcConnectionPool


def test_default_port_monitoring(tmpdir):

    f = Flow(monitoring=True).add(uses='jinahub+docker://SimpleIndexer')

    f.to_kubernetes_yaml(str(tmpdir))

    for file_path in ['executor0/executor0.yml', 'gateway/gateway.yml']:
        with open(f'{tmpdir}/{file_path}', 'r') as file:

            data_raw = file.read().split('---\n')
            data_yaml = [yaml.load(data, Loader=yaml.FullLoader) for data in data_raw]

            for data in data_yaml:

                if data['kind'] == 'Service':

                    assert (
                        data['spec']['ports'][1]['port']
                        == GrpcConnectionPool.K8S_PORT_MONITORING
                    )


def test_always_use_default_port_monitoring(tmpdir):

    f = Flow().add(uses='jinahub+docker://SimpleIndexer', port=8081)

    f.to_kubernetes_yaml(str(tmpdir))

    for file_path in ['executor0/executor0.yml', 'gateway/gateway.yml']:
        with open(f'{tmpdir}/{file_path}', 'r') as file:

            data_raw = file.read().split('---\n')
            data_yaml = [yaml.load(data, Loader=yaml.FullLoader) for data in data_raw]

            for data in data_yaml:

                if data['kind'] == 'Service':

                    assert (
                        data['spec']['ports'][0]['port'] == GrpcConnectionPool.K8S_PORT
                    )


def test_always_use_default_port(tmpdir):

    f = Flow().add(uses='jinahub+docker://SimpleIndexer', port=8081)

    f.to_kubernetes_yaml(str(tmpdir))

    for file_path in ['executor0/executor0.yml', 'gateway/gateway.yml']:
        with open(f'{tmpdir}/{file_path}', 'r') as file:

            data_raw = file.read().split('---\n')
            data_yaml = [yaml.load(data, Loader=yaml.FullLoader) for data in data_raw]

            for data in data_yaml:

                if data['kind'] == 'Service':

                    assert (
                        data['spec']['ports'][0]['port'] == GrpcConnectionPool.K8S_PORT
                    )

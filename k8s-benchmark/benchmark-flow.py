import click

from jina import Flow
from jina.enums import InfrastructureType


@click.command()
@click.option('--pool/--no-pool', default=True)
def benchmark(pool):
    f = Flow(
        name='flow',
        port_expose=8080,
        infrastructure=InfrastructureType.K8S,
        k8s_connection_pool=pool,
        static_routing_table=True,
    ).add(
        name='executor1',
        replicas=2,
        k8s_custom_resource_dir='template',
        uses='gcr.io/jina-showcase/dummy-executor',
    )

    f.start()


if __name__ == '__main__':
    benchmark()

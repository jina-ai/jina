import click

from jina import Flow
from jina.enums import InfrastructureType


@click.command()
@click.option('--pool/--no-pool', default=True)
def benchmark(pool):
    f = (
        Flow(
            name='flow',
            port_expose=8080,
            infrastructure=InfrastructureType.K8S,
            k8s_connection_pool=pool,
            static_routing_table=True,
        )
        .add(
            name='segmenter',
            replicas=2,
            k8s_custom_resource_dir='template',
            uses='gcr.io/jina-showcase/noop-executor',
        )
        .add(
            name='encoder',
            replicas=3,
            k8s_custom_resource_dir='template',
            uses='gcr.io/jina-showcase/noop-executor',
        )
        .add(
            name='indexer1',
            replicas=2,
            k8s_custom_resource_dir='template',
            uses='gcr.io/jina-showcase/dummy-executor',
        )
        .add(
            name='indexer2',
            replicas=2,
            k8s_custom_resource_dir='template',
            uses='gcr.io/jina-showcase/dummy-executor',
            needs='encoder',
        )
        .add(
            name='filter',
            replicas=1,
            k8s_custom_resource_dir='template',
            uses='gcr.io/jina-showcase/noop-executor',
            needs=['indexer1', 'indexer2'],
        )
    )

    f.start()


if __name__ == '__main__':
    benchmark()

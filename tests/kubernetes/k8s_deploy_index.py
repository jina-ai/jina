from typing import Dict

from jina import Flow

postgres_dns = f'postgres.postgres.svc.cluster.local'

postgres_config = {
    'hostname': postgres_dns,
    'port': 5432,
    'username': 'postgresadmin',
    'database': 'postgresdb',
}


def _get_postgres_config_for_table(table_name: str) -> Dict:
    cfg = postgres_config
    cfg['table'] = table_name
    return cfg


# kubernetes pod
# normal flow

GCP_REGISTRY_PROJECT_NAME = 'mystical-sweep-320315'
index_flow = (
    Flow(name='index-flow', port_expose=8080, protocol='http', infrastructure='k8s')
    .add(
        name='segmenter',
        uses=f'gcr.io/{GCP_REGISTRY_PROJECT_NAME}/doc-segmenter:v.0.0.1',
    )
    .add(
        name='textfilter',
        uses=f'gcr.io/{GCP_REGISTRY_PROJECT_NAME}/text-filter:v.0.0.2',
        needs='segmenter',
    )
    .add(
        name='textencoder', uses='jinahub+docker://CLIPTextEncoder', needs='textfilter'
    )
    .add(
        name='textstorage',
        uses='jinahub+docker://PostgreSQLStorage',
        uses_with=_get_postgres_config_for_table('text_data'),
        needs='textencoder',
    )
    .add(
        name='semanticsegmentimage',
        uses=f'gcr.io/{GCP_REGISTRY_PROJECT_NAME}/semantic-image-segmenter:v.0.0.2',
        needs='segmenter',
    )
    .add(
        name='imageencoder',
        uses='jinahub+docker://CLIPImageEncoder',
        needs='semanticsegmentimage',
    )
    .add(
        name='imagestorage',
        uses='jinahub+docker://PostgreSQLStorage',
        uses_with=_get_postgres_config_for_table('image_data'),
        needs='imageencoder',

    )
)
index_flow.plot('index-flow.jpg')
print('deploy index flow')
index_flow.start()

(docker-compose)=
# Jina with Docker Compose

Jina natively supports deploying your Flow and Executors locally with docker-compose.

## Preliminaries

Please first make sure [`Docker Compose`](https://docs.docker.com/compose/install/) is installed locally.

## Deploy your `Flow`

To deploy a `Flow` with `Docker Compose`, first, you need to generate a `yaml` file with all the Executors' services descriptions.
Then, you can use the `docker-compose up -f <file.yml>` command to start all the services and start accepting requests.

```{caution}
All Executors in the Flow should be used with `jinahub+docker://...` or `docker://...`.
```

To generate YAML configurations for Docker Compose from a Jina Flow, one just needs to call:

```python
flow.to_docker_compose_yaml('docker-compose.yml')
```

This will create a file 'docker-compose.yml' with all the services neeeded to compose and serve the Flow.

## Examples

### Indexing and searching images using CLIP image encoder and PQLiteIndexer

```{admonition} Caution
:class: caution
Before starting this example, make sure that CLIPImageEncoder and PQLiteIndexer images are already pulled to your local machine.

You can use:

`jina hub pull jinahub+docker://CLIPImageEncoder`
`jina hub pull jinahub+docker://PQLiteIndexer`
```

This example shows how to build and deploy a Flow with Docker Compose with [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q) as encoder and [`PQLiteIndexer`](https://hub.jina.ai/executor/pn1qofsj) as indexer.

```python
from jina import Flow

f = Flow(port_expose=8080, protocol='http').add(
    name='encoder', uses='jinahub+docker://CLIPImageEncoder', replicas=2
).add(name='indexer', uses='jinahub+docker://PQLiteIndexer', uses_with={'dim': 512}, shards=2)
```

Now, we can generate Docker Compose YAML configuration from the Flow:

```python
f.to_docker_compose_yaml('docker-compose.yml')
```

As you can see, the Flow contains services for the gateway and the rest of executors.

Now, you can deploy this Flow to you cluster in the following way:
```shell
docker-compose up -f docker-compose.yml
```

Once we see that all the Services in the Flow are ready, we can start sending index and search requests.

```python
import os

from jina.clients import Client
from jina import DocumentArray

client = Client(host='localhost', port=8080)
client.show_progress = True
indexing_documents = DocumentArray.from_files('./imgs/*.jpg')
indexed_documents = []
for resp in client.post(
    '/index', inputs=indexing_documents, return_results=True
):
    indexed_documents.extend(resp.docs)

print(f' Indexed documents: {[doc.uri for doc in indexed_documents]}')
query_doc = indexing_documents[0]
query_responses = client.post(
    '/search', inputs=query_doc, return_results=True
)

closest_match_uri = query_responses[0].docs[0].matches[0].uri
print('closest_match_uri: ', closest_match_uri)
```

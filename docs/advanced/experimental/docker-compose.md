(docker-compose)=
# Jina with Docker Compose

Jina is a cloud native neural search framework. Therefore, one of the simplest ways of either prototyping or serving in
production is to deploy your `Flow` with `docker-compose`.

Remember that a `Flow` defines complex processing pipelines. A `Flow` is composed of `Executors` which run python code
defined to operate on `DocumentArray`. These `Executors` will live in different runtimes depending on how you want to deploy
your Flow. By default, if you are serving your Flow locally they will live within processes. Nevertheless, 
because Jina is thought to be cloud native your Flow can easily manage Executors that live in containers and that are
orchestrated by your favorite tools. One of the simplest is `Docker Compose` which is supported out of the box. 

Under the hood with one line 
```python
flow.to_docker_compose_yaml('docker-compose.yml')
```

Jina will generate for you a `docker-compose.yml` config files that you can use directly with 
`docker-compose` which correspond to your `Flow`, avoiding you the overhead of defining the services for the gateway 
and the deployment of the `Flow`. 


## Examples : Indexing and searching images using CLIP image encoder and PQLiteIndexer


### Deploy your Flow


```{admonition} Caution
:class: caution
Please first make sure [`Docker Compose`](https://docs.docker.com/compose/install/) is installed locally.
```

```{admonition} Caution
:class: caution
Before starting this example, make sure that CLIPImageEncoder and PQLiteIndexer images are already pulled to your local machine.

You can use:

`jina hub pull jinahub+docker://CLIPImageEncoder`
`jina hub pull jinahub+docker://PQLiteIndexer`
```

This example shows how to build and deploy a Flow with Docker Compose with [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q)
as image encoder and [`PQLiteIndexer`](https://hub.jina.ai/executor/pn1qofsj) as indexer to perform fast nearest
neighbor retrieval on the images embedding.

```python
from jina import Flow

f = (
    Flow(port_expose=8080, protocol='http')
    .add(name='encoder', uses='jinahub+docker://CLIPImageEncoder', replicas=2)
    .add(
        name='indexer',
        uses='jinahub+docker://PQLiteIndexer',
        uses_with={'dim': 512},
        shards=2,
    )
)

```

Now, we can generate Docker Compose YAML configuration from the Flow:

```python
f.to_docker_compose_yaml('docker-compose.yml')
```

let's take a look at this config file:
```yaml
version: '3.3'
...
services:
  encoder-head:   # # # # # # # # # # # 
                  #                   #   
  encoder-rep-0:  #   Deployment 1    #
                  #                   #
  encoder-rep-1:  # # # # # # # # # # #

  indexer-head:   # # # # # # # # # # # 
                  #                   #   
  indexer-0:      #   Deployment 2    #
                  #                   #
  indexer-1:      # # # # # # # # # # #

  gateway: 
    ...
    ports:
    - 8080:8080
```

Here you can see that 7 services will be created.One for the `gateway` which is the entrypoint of the `Flow`. 
There are three services associated with the encoder, one for the Head and two for the Replicas. Same for the indexer, one for the Head and two for the Shards.

Now, you can deploy this Flow to your cluster:

```shell
docker-compose -f docker-compose.yml up
```

### Use your search engine and query your Flow

Now that your Flow is up and running in your docker compose you can to query it:

Once we see that all the Services in the Flow are ready, we can start sending index and search requests.

First let's define a client:
```python
from jina.clients import Client
from jina import DocumentArray

client = Client(host='localhost', protocol='http',port=8080)
client.show_progress = True
```

then let's index our set of images in which we want to search :

```{admonition} Caution
:class: caution
Before launching using you Flow please be sure to have several `jpg` images in the folder : `./imgs`
```

```python
indexing_documents = DocumentArray.from_files('./imgs/*.jpg').apply(
    lambda d: d.load_uri_to_image_tensor()
)

resp_index= client.post('/index', inputs=indexing_documents, return_results=True)

print(f'Indexed documents: {len(resp_index[0].docs)}')
```

Then let's search for the closest image of our query image

```python
query_doc = indexing_documents[0]
resp_query = client.post("/search", inputs=[query_doc], return_results=True)

matches = resp_query[0].docs[0].matches
print(f'Matched documents: {len(matches)}')
```



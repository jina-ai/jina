# Simple Text Search

Let's build a Flow that will index text Documents into an index so that we can then retrieve them using Jina framework and run in Kubernetes.

We will see:
 - How to create a custom Executor
 - How to publish privately to Jina Hub
 - How to build your Flow locally combining different Executors
 - How to deploy it in Kubernetes

For that we want to build a Flow that looks like this:

```{figure} simple_flow_walkthrough.svg
:width: 70%

```

In this case, we are going to see how to build a Flow when we will use a public Executor from the `Hub` and a private Executor built and developed by us.

We will use the `SimpleIndexer` from the `Hub` and we will use an `EncodingExecutor` ourselves.

You can check more detailed information about Executors in our Documentation (https://docs.jina.ai/fundamentals/executor/#executor)

## Write our own Executor

Since we want to write our own Executor so that it can be easily containerized and deployed in Kubernetes, we are going to use `jinahub` to create it.

## Create the Executor project (https://docs.jina.ai/fundamentals/executor/hub/create-hub-executor/#create)

First we are going to use `jina hub new` command line to create a project template so that we can complete our project.

```bash 
jina hub new --name my_encoding_executor
```

We can then complete the dialog to fill some of the information for the template. 

In this case, when the dialog asks:

- ❔ Or do you want to proceed to advanced configuration [y/n] (n): y
We will answer yes.

And then, when we are asked:
- ❔ Do you need to write your own Dockerfile instead of the auto-generated one? [y/n] (n): y
We will answer yes.

This is needed because we want to do a little tweak to the Dockefile so that the experience in K8s is smoother.

After this we can see the following structure:

```
__my_encoding_executor
  |
  |__config.yml # configuration of the Executor to be put in a Flow
  |__Dockerfile # Dockerfile dumped by the jina hub new
  |__executor.py # source code of the Executor
  |__manifest.yml # manifest for better UI in the Hub
  |__README.md # documentation that will appear in the Hub UI, Document the behavior and usage of the Executor
  |__requirements.txt # requirements files with the extra requirements besides Jina that the executor needs
```

## Write the Executor logic

Let's write our own `Executor`. Executors in Jina are objects that expose endpoints in a Pythonic way to work on `DocumentArrays` objects. One can see `Executors` as Pythonic microservices who "speak" DocumentArray as a mean of communication with each other.

In this case we will have a very simple Executor that will get a transformer model and embed each Document using this model.

We are going to create our `executor` in the `executor.py` inside the project

```python
from jina import Executor, DocumentArray, requests  # Importing required modules and classes from Jina

from sentence_transformers import \
    SentenceTransformer  # Import extra packages needed to implement the specific logic of this microservice


class MyEncodingExecutor(Executor):
    """Encoding Executor using sentence transformers"""

    def __init__(self, model_name: str = 'albert-base-v2', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SentenceTransformer(model_name)

    @requests  # Methods decorated with @requests are mapped to network endpoints while serving. (
    # https://docs.jina.ai/fundamentals/executor/executor-methods/#requests-methods)
    def encode(self, docs: DocumentArray, **kwargs):
        docs.embeddings = self.model.encode(
            docs.texts)  # compute all the embeddings of all Documents in DocArray and assign to embeddings
```

Now we can try to validate the logic of our Executor by using the Executor locally as a regular Python class.

```python
from executor import MyEncodingExecutor
from docarray import DocumentArray, Document

docs = DocumentArray([Document(text='first text that I want to encode'), Document(text='second text that I want to encode')])

executor = MyEncodingExecutor()

executor.encode(docs)

for doc in docs:
    print(f' doc with text {doc.text} was encoded to a vector of shape {doc.embedding.shape}')
```

## Tweak the Dockerfile

In order to have the Executor start without needing to download the model from the internet, we are going to cache the model when building the docker image.

To achieve this, we are going to edit the `Dockerfile` and edit to this.

```Dockerfile
FROM jinaai/jina:latest

# install requirements before copying the workspace
COPY requirements.txt /requirements.txt
RUN pip install --default-timeout=1000 --compile -r requirements.txt

# setup the workspace
COPY . /workspace
WORKDIR /workspace

RUN python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("albert-base-v2")'

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
```

Note that: `RUN python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("albert-base-v2")'` is the only step added by us.

## Push Executor to the Hub

Once we are sure this works locally, we want to have this Executor part of a Jina Flow (https://docs.jina.ai/fundamentals/flow/#flow). Since we want this later to be deployed in Kubernetes,
we want to containerize this Executor so that is ready to be used and deployed anywhere.

Since this Executor logic not only depends on Jina Framework but it also leverages `sentence-transformers`, we need to include this information in the `requirements.txt` inside the Executor project.


```requirements.txt
sentence-transformers>=2.2.0
```

Once we have all this project set up. We are going to publish this Executor to the Hub privately so that no one other than use can see it.

**note** We are going to soon include a feature that will let you push this Executor to a private registry.

To push it privately, run
```bash
jina hub push --private MyEncodingExecutor
```


Then this process may take some time and it will give you some NAME and SECRET which you need to keep in order to use it later.

You should see something like this:

```text
╭────────────────────────── Published ──────────────────────────╮
│                                                               │
│   📛 Name         MyEncodingExecutor                          │
│   🔗 Hub URL      https://hub.jina.ai/executor/5o2vlu2l/      │
│   🔒 Secret       bdfa0f45e0d1f1c0a722a1b71479e336            │
│                   ☝️ Please keep this token in a safe place!   │
│   👀 Visibility   private                                     │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

Since this take a little while, I have done this in advance and kept the NAME and SECRET.



## Build the Flow.

Once we have our Executor, we can start thinking on how to create our Executor. For this Flow we are going to combine 2 Executors.

1 - Our own private Executor that we just published
2 - An AnnLiteIndexer used from our Public Hub (https://hub.jina.ai/executor/7yypg8qk) which enables filtering

To build this Flow we can use `python` or `yaml`. In this example we are going to use `python`. (https://docs.jina.ai/fundamentals/flow/add-executors/#add-executors)

We are going to use a Flow where we will index some Documents and do neural search on them and filter on `shorts` items.


```python
from jina import Flow, DocumentArray, Document

f = Flow().add(uses='jinahub+docker://MyEncodingExecutor:bdfa0f45e0d1f1c0a722a1b71479e336', name='encoder').add(
    uses='jinahub+docker://AnnLiteIndexer', uses_with={
        'n_dim': 768,
        'columns': [('item', 'str')],
    }, name='indexer')

index_document_array = DocumentArray([Document(text='Description of shorts 1', tags={'item': 'shorts'}),
                                      Document(text='Description of shorts 2', tags={'item': 'shorts'}),
                                      Document(text='Description of jacket 1', tags={'item': 'jacket'}),
                                      Document(text='Description of jacket 2', tags={'item': 'jacket'})])

query_document_array = DocumentArray(Document(text='searching for valves'))

with f:
    f.post(on='/index', inputs=index_document_array)  # Index these 4 documents
    ret = f.post(on='/search', inputs=query_document_array,
                 parameters={'filter': {'item': {'$eq': 'shorts'}}})  # Query with parameters
    print(f' the search returned {len(ret[0].matches)} matches')  # Only 2 elements
    for i, match in enumerate(ret[0].matches):
        print(f' Result {i} => {match.text}')
```

## Deploy to Kubernetes (https://docs.jina.ai/how-to/kubernetes/#deploy-with-kubernetes)

Up until now we have shown how to build a Flow and see how it works locally.

Now we are going to see how to deploy to Kubernetes. We are going to try to deploy into a local K8s cluster (minikube) but this can easily translated into any K8s cluster.

### Conver Flow to K8s

```python
from jina import Flow, DocumentArray, Document

f.to_kubernetes_yaml('./k8s_flow', k8s_namespace='custom-namespace')
```

You should expect the following file structure to be generated

```
.
└── k8s_flow
    ├── gateway
    │   └── gateway.yml
    └── encoder
    │   └── encoder.yml
    └── indexer
        └── indexer.yml
``` 


### Start minikube

Assuming that you installed `minikube`

```bash
minikube start
```

### Deploy Flow in Kubernetes
Create the custom-namespace

```
kubectl create namespace custom-namespace
```

Deploy the Flow

```
kubectl apply -R -f ./k8s_flow
```

Let's check that the Pods are created and wait for them to be ready

```
kubectl get pods -n custom-namespace
```

Note down the name of the gateway Pod so that we can target from the Client


Note that the Jina gateway was deployed with name gateway-7df8765bd9-xf5tf.

### Index and search

```python
import portforward

from jina.clients import Client
from docarray import DocumentArray, Document

index_document_array = DocumentArray([Document(text='Description of shorts 1', tags={'item': 'shorts'}), Document(text='Description of shorts 2', tags={'item': 'shorts'}),
        Document(text='Description of jacket 1', tags={'item': 'jacket'}), Document(text='Description of jacket 2', tags={'item': 'jacket'}) ])

query_document_array = DocumentArray(Document(text='searching for valves'))

with portforward.forward('custom-namespace', 'gateway-5bb55fb998-dfxxf', 8080, 8080):
    client = Client(host='localhost', port=8080)
    client.show_progress = True
    client.post(
        '/index',
        inputs=index_document_array,
    )
    ret = client.post(on='/search', inputs=query_document_array, parameters={'filter': {'item': {'$eq': 'shorts'}}}) # Query with parameters
    print(f' the search returned {len(ret[0].matches)} matches') # Only 2 elements 
    for i, match in enumerate(ret[0].matches):
        print(f' Result {i} => {match.text}')
```

Now you know how to build and deploy a Jina application in Kubernetes. 
We have learned:
- How to write our business logic as an Executor to be served as a microservice
- How to containerize it with the help of Jina Hub
- How to build a Flow with this Executor combining other Executors from the Hub
- Deploy this Flow in the Hub

Future work:

- If you want to understand how to scale it with the help of Kubernetes check the documentation (https://docs.jina.ai/how-to/kubernetes/#scaling-executors-flow-with-replicas-and-shards)
- If your Executor needs some specific dependencies or some specific Dockerfile, you can learn how to dockerize and use your containers without the need of Hub at https://docs.jina.ai/fundamentals/executor/containerize-executor/#containerize

# Sneak Peek into MultiModality

So far we have seen how to work with a single modality. It turns out that to work with multimodality in Jina is not so different, as the language Jina "speaks" is DocumentArray which offers a convenient API for this purpose.

You can take a look on how `dataclass` works from DocumentArray https://docarray.jina.ai/fundamentals/dataclass/#dataclass and how it is related to the nested structure of Document https://docarray.jina.ai/fundamentals/document/nested/#recursive-nested-document.

This will allow to represent a high-level `Document` as a PDF into a set of lower-level `Documents` as `images` and `texts` that can be considered independently and in groups as DocArray API offers.

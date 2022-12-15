# Search Similar Images

Given an example image can we find similar images without the need of any labels? Leveraging Jina, we have the advantage that 
we don't need to use any labels or textual information about the images in order to build a search for similar images.

In this tutorial we are going to create an image search system that retrieves similar images. We are going to
use the test split of the [Dogs vs. Cats](https://www.kaggle.com/c/dogs-vs-cats/data?select=test1.zip) dataset, which we
will subsequently refer to as the pets dataset. It contains 12.5K images of cats and dogs. Now, we can define our
problem as selecting an image of cat or dog, and getting back images of similar cats or dogs respectively.

Jina searches semantically, and the results will vary depending on the neural network that we use for image encoding. Our
task is to search for similar images so, we will consider visually-similar images as semantically-related.

```{tip}
The full source code of this tutorial is available in this [Google Colab notebook](https://colab.research.google.com/drive/1JUWCZRH88uAvofUomTZYxvIR2jSm7H6Z?usp=sharing)
```

## Pre-requisites

Before we begin building our Flow we need to do a few things. 

* Install the following dependencies.

```shell
pip install jina "lightning-flash[image]==0.5.0" "vissl" "fairscale" pytorch-lightning==1.4.9
```

* Download [the dataset](https://www.kaggle.com/c/dogs-vs-cats/data?select=test1.zip) and unzip it.

You can use the link or the following commands:
```shell
gdown https://drive.google.com/uc?id=1T8IzCJDf3qNBq2Lg2vRKsNV0StOFeOVR
unzip test1.zip
```

## Build the Flow

The solution uses a simple pipeline that can be subdivided into two steps:  **Index** and **Query**

### Index

To search something out of the full dataset, we first need to index the data. This means that we store the embeddings
of all the images from the dataset in some form of storage. The images can be read as a numpy array which is then
fed to the neural network of our choice. This neural network encodes the input images into some latent space which we call
"embeddings". We then use an **Indexer** to store these embeddings in memory.

### Query

Once the data is indexed, i.e. our database is built, we simply need to feed our query (an image or set of
images) to the model to encode it into embeddings and then use the **Indexer** to retrieve matching images. The matching
can be based on any type of metric but without going deeper into this, we will focus only on Euclidean distance between
two embeddings (corresponding to two images).

We will use the **SimpleIndexer** Executor as
our indexer (the one that stores and retrieves data). This Executor also returns the matching `Document` when we make
a query. The search part is done using the built-in `match` function of `DocumentArrayMemmap`. To encode the images into
embeddings we will use our own Executor which uses the pre-trained 'ResNet101' model.

## Flow Overview

We have one Flow defined for this tutorial. However, it handles requests to `/index` and `/search` differently by
defining different endpoints using `requests` decorators. Below we see the Flow, which consists of an `Encoder` to encode
the images as the first step, followed by an `Indexer` to store/retrieve data.

```{figure} ../../../.github/images/image_search_flow.svg
:align: center
```

## Insights

Our first task is to wrap the image data as `Document`s and form a `DocumentArray`. This can be done easily with the
following code snippet. `from_files` creates an iterator over a list of image paths and yields `Document`s:

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

docs_array = DocumentArray(from_files(f'{image_dir}/*.{image_format}'))
```

Once the image is loaded our next step is to encode these images into embeddings. As stated earlier you can use
Executors from [Jina Hub](https://hub.jina.ai) off-the-shelf or you can define an Executor of your own in
just a few steps. For this tutorial we will write our own Executor:

```python
from jina import DocumentArray, Executor, requests
from flash.image import ImageEmbedder


class FlashImageEncoder(Executor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._embedder = ImageEmbedder(embedding_dim=1024)

    @requests
    def predict(self, docs: DocumentArray, **kwargs):
        embeds = self._embedder.predict(docs.get_attributes('uri'))
        for doc, embed in zip(docs, embeds):
            doc.embedding = embed.numpy()
```

To build an Encoder Executor we inherit the base `Executor` and use a decorator
to define endpoints. As this `request` decorator is empty, this function will be called regardless of the
endpoints invoked, i.e., on both the `/index` and `/search` endpoints. We
leverage [lightning-flash](https://github.com/PyTorchLightning/lightning-flash) to use the pre-trained `ResNet101` model for
getting the embeddings. You can replace this model with any other pre-trained models of your choice. When this
Executor is instantiated, the pre-trained weights are downloaded automatically. The `predict` function takes in
the `DocumentArray` and extracts embeddings, each of which is then stored in the `embedding` attribute of the
respective `Document`.

Finally, comes the storage/retrieval step. We do this with the **Indexer** Executor. You can use any of the
available indexers on [Jina Hub](https://hub.jina.ai) or define your own. To create an **Indexer** you need to have two
endpoints: `/index` and `/search`. For this tutorial we will define a `SimpleIndexer` which is [also available on jina
Hub](https://hub.jina.ai/executor/zb38xlt4).

```python
from jina import DocumentArrayMemmap, DocumentArray, Executor, requests


class SimpleIndexer(Executor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dam = DocumentArrayMemmap(self.workspace)

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._dam.extend(docs)

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        docs.match(self._dam)
```

`SimpleIndexer` stores all the Documents with a memory map when invoked with the `/index` endpoint. During the search
Flow, it matches the query `Document` with the indexed `Document` using the built-in `match` function
of `DocumentArrayMemmap`.

## Putting it all together in a Flow

So far we saw individual components of the Flow and how to define them. Next comes putting all of this together in a Flow:

```python
from jina import Flow

f = (
    Flow(cors=True, port_expose=12345, protocol="http")
        .add(uses=FlashImageEmbedder, name="Encoder")
        .add(uses=SimpleIndexer, name="Indexer")
)
```

### Start the Flow and Index data

```python
with f:
    f.post('/index', docs_Array)
    f.block()
```

### Query from Python

Keeping the server running we can start a simple client to make a query:

```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["cosine"].value:2f}: "{d.uri}"')


c = Client(protocol='http', port=12345)  # connect to localhost:12345
c.post('/search', Document(uri='path/to/an/image/'), on_done=print_matches)
```

## Results

The returned response contains the matching `Document` which in turn contains the `uri` of the images. Below we can see the
returned matching images of the query:

```{figure} image-search.png
:align: center
```

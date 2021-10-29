# Search Similar Images

Given an example image can we find similar images without the need of any labels? Leveraging Jina, the advantage that we
get is that we do not need to use any labels or textual information about the images in order to build similar image
search.

In this tutorial we are going to create an image search system that retrieves similar images. The data we are going to
use is the test split of the [Dogs vs. Cats](https://www.kaggle.com/c/dogs-vs-cats/data?select=test1.zip) datasets. We
will subsequently refer this dataset as pets dataset. It contains 12.5K images of cats and dogs. Now, we can define our
problem as selecting an image of cat or dog, we would like to get similar images of cats or dogs respectively.

We know that Jina searches semantically and this could vary with the neural network that we use for encoding. Since our
task is to search similar images we will consider visually similar as semantically-related.

## Build the Flow

The solution to the problem entails a simple pipeline that can be subdivided into two steps:  **Index** and **Query**

### Index

To search something out of the full data, first we need to index the data. What it means is that we store the embeddings
of all the images from the pets dataset in some form of storage. The images can be read as a numpy array which is then
fed to neural network of our choice. This neural network encodes the input images into some latent space which we call
as embeddings. We then use **Indexer** to store these embeddings in memory.

### Query

Once the data is indexed, i.e. our database is built, we simply need to feed our query which is an image or set of
images to the model to encode it into embeddings and then use the **Indexer** to retrieve matching images. The matching
can be based on any type of metrics but without going deeper into this, we will focus only on euclidean distance between
two embeddings (corresponding to two images) as metrics.

Now, one might think what this *Indexer* is, or how to use neural network of our choice. Worry not, we've got you
covered. In Jina AI, we have three fundamental concepts which is all you need to know to follow this tutorial. If you
haven't read it yet, head on to [Jina's docs](https://docs.jina.ai/) page and give it a shot. Executor is the
algorithmic unit in the Jina. It performs a single task on a `Document` or `DocumentArray`.

We have many executors available at [Jina Hub](https://hub.jina.ai) - a marketplace for Executors. You can use any of
them relevant to your tasks or build one of your own. Coming back to problem, we will use **SimpleIndexer** executor as
our indexer (the one that stores and retrieves data). This executor also returns us the matching `Document` when we make
a query. The search part is done using the built-in `match` function of `DocumentArrayMemmap`. To encode the images into
embeddings we will use our own defined executor which uses pre-trained 'ResNet101' model.

## Flow Overview

We have one flow defined for this tutorial, however, it handles requests to `/index` and `/search` differently by
defining different endpoints using `requests` decorators. Below we see the Flow, which consists of `Encoder` to encode
the images as first step, followed by an `Indexer` to store/retrieve data.

```{figure} ../../.github/images/image_search_flow.svg
:align: center
```

## Insights

Our firs task is to wrap the image data as `Document` and form a `DocumentArray`. This can be easily done by using
following code snippet. `from_files` creates an iterator over a list of image path provided and yields `Document`.

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

docs_array = DocumentArray(from_files(f'{image_dir}/*.{image_format}'))
```

Once the image is loaded our next step is to encode these images into embeddings. As stated earlier one can use
executors from  [hub.jina.ai](https://hub.jina.ai) and use them off-the-shelf or can define an executor of their own in
just few steps. For this tutorial we will write our own executor in few lines of codes as shown below.

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

As one can see, how simple it is to build an `Encoder` executor. We simply inherit the base `Executor` and use decorator
to define endpoints. As this `request` decorator is empty, it means that this function will be called regardless of the
endpoints invoked, i.e., on both `/index` and `/search` endpoint. We
leverage [lightning-flash](https://github.com/PyTorchLightning/lightning-flash) to use pre-trained `ResNet101` model for
getting the embeddings. Reader can replace this model with any other pre-trained models of their choice. When this
executor is instantiated, the pre-trained weights are downloaded automatically. The `predict` function takes in
the `DocumentArray` and extracts embeddings which is then stored in the `embedding` attribute of the
respective `Document`.

Finally, comes the storage/retrieval step. This we accomplish using an **Indexer** executor. We can use any of the
available indexers on [hub.jina.ai](https://hub.jina.ai) or define our own. To create an **Indexer** we need to have two
endpoints `/index` and `/search`. For this tutorial we will define a `SimpleIndexer` which is also available on jina
hub.

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

`SimpleIndexer` stores all the Documents with a memory map when invoked with a `/index` endpoint. During the search
flow, it matches the query `Document` with the indexed `Document` using the built-in `match` function
of `DocumentArrayMemmap`.

## Putting it all together in a Flow

So far we saw individual components of the Flow and how to define them. Next comes putting all this together in a Flow,
which can be done as shown below

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

Keeping the server running we can start a simple client to make query.

```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["euclidean"].value:2f}: "{d.text}"')


c = Client(protocol='http', port=12345)  # connect to localhost:12345
c.post('/search', Document(text='request(on=something)'), on_done=print_matches)
```

## Results

The returned response contains the matching `Document` which contains the `uri` of the images. Below we can see the
returned matching images to the query

```{figure} image-search.png
:align: center
```
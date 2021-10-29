# Search Similar Images

We all have used text-based search system. We enter text and Voila! We get the results, some desirbale and some not so
much. However, I am totally convinced that at some point we all have definitely pondered over whether searching with
different data modalities such as images, video, audio, etc. is possible or not. Worry not! Here at Jina AI we aim to
achieve the impossible.

One can easily build search system using Jina AI which can search any **kind** of data. In this tutorial, we will see
how to build an Image-to-Image search system leveraging Jina.

### Problem Formulation

Given an example image can we find similar images without the need of any labels? Using Jina, the advantage that we get
here is that we do not need to use any labels or textual information about the images. The data we are going to use is
the test split of the [Dogs vs. Cats](https://www.kaggle.com/c/dogs-vs-cats/data?select=test1.zip) datasets. We will
subsequently refer this dataset as pets dataset. It contains 12.5K images of cats and dogs. Now we can define our
problem as selecting an image of cat or dog, we would like to get similar images of cats or dogs respectively.

We know that Jina searches semantically and this could vary with the neural network that we use for encoding. Since our
task is to search similar images we will consider semantically-related as visuall similar

### Build the Flow

The solution to the problem entails simple pipeline that can be subdivided into two steps:  **Index** and **Query**

#### Index

To search something out of the full data, first we need to index the data. What it means is that we store the encodings
of all the images from the pets dataset in some form of storage. The images can be read as a numpy array which is then
fed to neural network of our choice. This neural network encodes the input images into some latent space which we also
call as embeddings. We then use **Indexer** to store these embeddings in memory.

#### Query

Once the data is indexed, i.e. our database is built, we simply need to feed our query which is an image or set of
images to the model to encode it and then use the **Indexer** to retrieve matching images. The matching can be based on
any type of metrics but without going deeper into this, we will focus only on euclidean distance between two
embeddings (correpsonding to two images) as metrics.

Now, one might think what this *Indexer* is, or how to use neural network of our choice. Worry not, we've got you
covered. In Jina AI, we have three fundamental concepts which is all you need to know to follow this tutorial. If you
haven't read it yet, head on to [Jina's docs](https://docs.jina.ai/) page and give it a shot. Executor is the
algorithmic unit in the Jina. It performs a single task on a `Document` or `DocumentArray`.

We have many executors available at Jina Hub - a marketplace for Executors. You can use any of them relevant to your
tasks or build one of your own. Coming back to problem, we will use **SimpleIndexer** executor as our indexer (the one
that stores data). This executor also returns us the matching `Document` when we make a query. The search part is done
using the built-in `match` function of `DocumentArrayMemmap`. To encode the images into embeddings we will use our own
defined executor which uses pre-trained 'ResNet101' model.

### Flow Overview

We have one flow defined for this tutorial, however, it handles requests to `/index` and `/search` differently by
defining different endpoints using `requests` decorators. Below we see the Flow, which consists of first step as
ImageNormalizer, then an Encoder to encode the images and finally an **Indexer** to store/retrieve data

```{figure} ../../.github/images/image_search_flow.svg
:align: center
```

### Insights

Our firs task is to wrap the image data as `Document` and form a `DocumentArray`. This can be easily done by using
following code snippet. `from_files` creates an iterator over a list of image path provided and yields `Document`.

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

docs_array = DocumentArray(from_files(f'{image_dir}/*.{image_format}'))
```

Once the image is loaded we then do some normalization. For this we can
use [`ImageNormalizer`](https://hub.jina.ai/executor/dzrova7k) executor which handles the image pre-processing step. It
can resize, crops, and normalize images. Although one can make it as a separate executor, it is recommended to use
pre=processing as part of the `encoding` step, since normalization is highly dependent on the model.

Our next step of the flow is to encode the pre-processed images. As stated earlier one can use executors
from  [hub.jina.ai](https://hub.jina.ai) and use them off-the-shelf or can define an executor of their own in just few
steps.

```python
from jina import DocumentArray, Executor, requests
from flash.image import ImageEmbedder


class FlashImageEncoder(Executor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._embedder = ImageEmbedder(embedding_dim=1024)

    @requests
    def predict(self, docs: DocumentArray, **kwargs):
        embd = self._embedder.predict(docs.get_attributes('blob'))
        for doc, _embd in zip(docs, embd):
            doc.embedding = _embd.numpy()
```

As one can see, how simple it is to build an encoder executor. We simply inherit the base `Executor` and use decorator
to define endpoints. As this `request` decorator is empty, it means that this function will be called regardless of the
endpoints invoked, i.e., on both `/index` and `/search` endpoint. We
leverage [lightning-flash](https://github.com/PyTorchLightning/lightning-flash) to use pre-trained `ResNet101` model for
encoding. Reader can replace this model with any other pre-trained models of their choice. When this executor is
instantiated, the pre-trained weights are downloaded automatically. The `predict` function takes in the `DocumentArray`
and extracts embeddings which is then stored in the `embedding` attribute of the respective `Document`

FInally, comes the storage/retrieval step. This we accomplish using an **Indexer** executor. We can use any of the
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








# Jina Code Snippets

These code snippets provide a short introduction to Jina's functionality and design framework. To run a snippet in a Jupyter Notebook, just click the "run" button next to the snippet.

|     |   |
| --- |---|
| 🥚  | [CRUD Functions](#crud-functions) • [Document](#document) • [Flow](#flow)  |
| 🐣  | [Feed Data](#feed-data) • [Fetch Result](#fetch-result) • [Add Logic](#add-logic) • [Inter & Intra Parallelism](#inter--intra-parallelism) • [Decentralize](#decentralized-flow) • [Asynchronous](#asynchronous-flow) |
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [Flow Optimization](#flow-optimization) • [REST Interface](#rest-interface) |

## 🥚 Fundamentals

### CRUD Functions
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-basic-crud-functions.ipynb)



First we look at basic CRUD operations. In Jina, CRUD corresponds to four functions: `index` (create), `search` (read), `update`, and `delete`. With Documents below as an example:
```python
import numpy as np
from jina import Document
docs = [Document(id='🐲', embedding=np.array([0, 0]), tags={'guardian': 'Azure Dragon', 'position': 'East'}),
        Document(id='🐦', embedding=np.array([1, 0]), tags={'guardian': 'Vermilion Bird', 'position': 'South'}),
        Document(id='🐢', embedding=np.array([0, 1]), tags={'guardian': 'Black Tortoise', 'position': 'North'}),
        Document(id='🐯', embedding=np.array([1, 1]), tags={'guardian': 'White Tiger', 'position': 'West'})]
```

Let's build a Flow with a simple indexer:

```python
from jina import Flow
f = Flow().add(uses='_index')
```

`Document` and `Flow` are basic concepts in Jina, which will be explained later. `_index` is a built-in embedding + structured storage that you can use out of the box.

<table>
  <tr>
    <td>
    <b>Index</b>
    </td>
    <td>

```python
# save four docs (both embedding and structured info) into storage
with f:
    f.index(docs, on_done=print)
```

</td>
</tr>
  <tr>
    <td>
    <b>Search</b>
    </td>
    <td>

```python
# retrieve top-3 neighbours of 🐲, this print 🐲🐦🐢 with score 0, 1, 1 respectively
with f:
    f.search(docs[0], top_k=3, on_done=lambda x: print(x.docs[0].matches))
```

<sup>

```json
{"id": "🐲", "tags": {"guardian": "Azure Dragon", "position": "East"}, "embedding": {"dense": {"buffer": "AAAAAAAAAAAAAAAAAAAAAA==", "shape": [2], "dtype": "<i8"}}, "score": {"opName": "NumpyIndexer", "refId": "🐲"}, "adjacency": 1}
{"id": "🐦", "tags": {"position": "South", "guardian": "Vermilion Bird"}, "embedding": {"dense": {"buffer": "AQAAAAAAAAAAAAAAAAAAAA==", "shape": [2], "dtype": "<i8"}}, "score": {"value": 1.0, "opName": "NumpyIndexer", "refId": "🐲"}, "adjacency": 1}
{"id": "🐢", "tags": {"guardian": "Black Tortoise", "position": "North"}, "embedding": {"dense": {"buffer": "AAAAAAAAAAABAAAAAAAAAA==", "shape": [2], "dtype": "<i8"}}, "score": {"value": 1.0, "opName": "NumpyIndexer", "refId": "🐲"}, "adjacency": 1}
```
</sup>
</td>
</tr>
  <tr>
    <td>
    <b>Update</b>
    </td>
    <td>

```python
# update 🐲 embedding in the storage
docs[0].embedding = np.array([1, 1])
with f:
    f.update(docs[0])
```
</td>
</tr>
  <tr>
    <td>
    <b>Delete</b>
    </td>
    <td>

```python
# remove 🐦🐲 Documents from the storage
with f:
    f.delete(['🐦', '🐲'])
```
</td>
</tr>
</table>

For further details about CRUD functionality, checkout [docs.jina.ai.](https://docs.jina.ai/chapters/crud/)


### Document
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-construct-document.ipynb)

`Document` is [Jina's primitive data type](https://hanxiao.io/2020/11/22/Primitive-Data-Types-in-Neural-Search-System/#primitive-types). It can contain text, image, array, embedding, URI, and be accompanied by rich meta information. To construct a Document, you can use:

```python
import numpy
from jina import Document

doc1 = Document(content=text_from_file, mime_type='text/x-python')  # a text document contains python code
doc2 = Document(content=numpy.random.random([10, 10]))  # a ndarray document
```

A Document can be recursed both vertically and horizontally to have nested Documents and matched Documents. To better see the Document's recursive structure, you can use `.plot()` function. If you are using JupyterLab/Notebook, all Document objects will be auto-rendered.

<table>
  <tr>
    <td>

```python
import numpy
from jina import Document

d0 = Document(id='🐲', embedding=np.array([0, 0]))
d1 = Document(id='🐦', embedding=np.array([1, 0]))
d2 = Document(id='🐢', embedding=np.array([0, 1]))
d3 = Document(id='🐯', embedding=np.array([1, 1]))

d0.chunks.append(d1)
d0.chunks[0].chunks.append(d2)
d0.matches.append(d3)

d0.plot()  # simply `d0` on JupyterLab
```

</td>
<td>
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/four-symbol-docs.svg?raw=true"/>
</td>
</tr>
</table>

<details>
  <summary>Click here to see more about MultimodalDocument</summary>


### MultimodalDocument

A `MultimodalDocument` is a document composed of multiple `Document` from different modalities (e.g. text, image, audio).

Jina provides multiple ways to build a multimodal Document. For example, you can provide the modality names and the content in a `dict`:

```python
from jina import MultimodalDocument
document = MultimodalDocument(modality_content_map={
    'title': 'my holiday picture',
    'description': 'the family having fun on the beach',
    'image': PIL.Image.open('path/to/image.jpg')
})
```

One can also compose a `MultimodalDocument` from multiple `Document` directly:

```python
from jina.types import Document, MultimodalDocument

doc_title = Document(content='my holiday picture', modality='title')
doc_desc = Document(content='the family having fun on the beach', modality='description')
doc_img = Document(content=PIL.Image.open('path/to/image.jpg'), modality='image')
doc_img.tags['date'] = '10/08/2019'

document = MultimodalDocument(chunks=[doc_title, doc_description, doc_img])
```

#### Fusion Embeddings from Different Modalities

To extract fusion embeddings from different modalities Jina provides `BaseMultiModalEncoder` abstract class, which has a unique `encode` interface.

```python
def encode(self, *data: 'numpy.ndarray', **kwargs) -> 'numpy.ndarray':
    ...
```

`MultimodalDriver` provides `data` to the `MultimodalDocument` in the correct expected order. In this example below, `image` embedding is passed to the encoder as the first argument, and `text` as the second.

```yaml
jtype: MyMultimodalEncoder
with:
  positional_modality: ['image', 'text']
requests:
  on:
    [IndexRequest, SearchRequest]:
      - jtype: MultiModalDriver {}
```

Interested readers can refer to [`jina-ai/example`: how to build a multimodal search engine for image retrieval using TIRG (Composing Text and Image for Image Retrieval)](https://github.com/jina-ai/examples/tree/master/multimodal-search-tirg) for the usage of `MultimodalDriver` and `BaseMultiModalEncoder` in practice.

</details>

### Flow
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-create-flow.ipynb)

Jina provides a high-level Flow API to simplify building CRUD workflows. To create a new Flow:

```python
from jina import Flow
f = Flow().add()
```

This creates a simple Flow with one [Pod](https://101.jina.ai/#pod). You can chain multiple `.add()`s in a single Flow.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-visualize-a-flow.ipynb)

To visualize the Flow, simply chain it with `.plot('my-flow.svg')`. If you are using a Jupyter notebook, the Flow object will be displayed inline *without* `plot`.

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-flow0.svg?raw=true"/>

`Gateway` is the entrypoint of the Flow.

Get the vibe? Now we're talking! Let's learn more about the basic concepts and features of Jina:

---

|     |   |
| --- |---|
| 🥚  | [CRUD Functions](#crud-functions) • [Document](#document) • [Flow](#flow)  |
| 🐣  | [Feed Data](#feed-data) • [Fetch Result](#fetch-result) • [Add Logic](#add-logic) • [Inter & Intra Parallelism](#inter--intra-parallelism) • [Decentralize](#decentralized-flow) • [Asynchronous](#asynchronous-flow) |
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [Flow Optimization](#flow-optimization) • [REST Interface](#rest-interface) |


## 🐣 Basic

### Feed Data
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-feed-data.ipynb)

To use a Flow, open it via `with` context manager, like you would open a file in Python. Now let's create some empty Documents and index them:

```python
from jina import Document

with Flow().add() as f:
    f.index((Document() for _ in range(10)))
```

Flow supports CRUD operations: `index`, `search`, `update`, `delete`. In addition, it also provides sugary syntax on `ndarray`, `csv`, `ndjson` and arbitrary files.


<table>
<tr>
    <td>
    Input
    </td>
    <td>
     Example of <code>index</code>/<code>search</code>
    </td>
<td>
Explain
</td>
</tr>
  <tr>
    <td>
    <code>numpy.ndarray</code>
    </td>
    <td>
      <sup>

```python
with f:
  f.index_ndarray(numpy.random.random([4,2]))
```

</sup>
  </td>
<td>

Input four `Document`s, each `document.blob` is an `ndarray([2])`

</td>
</tr>
<tr>
    <td>
    CSV
    </td>
    <td>
      <sup>

```python
with f, open('index.csv') as fp:
  f.index_csv(fp, field_resolver={'pic_url': 'uri'})
```

</sup>
  </td>

<td>

Each line in `index.csv` is constructed as a `Document`, CSV field `pic_url` mapped to `document.uri`.

</td>
</tr>

<tr>
    <td>
    JSON Lines/<code>ndjson</code>/LDJSON
    </td>
    <td>
<sup>

```python
with f, open('index.ndjson') as fp:
  f.index_ndjson(fp, field_resolver={'question_id': 'id'})
```

</sup>
  </td>
<td>

Each line in `index.ndjson` is constructed as a `Document`, JSON field `question_id` mapped to `document.id`.

</td>
</tr>
<tr>
    <td>
    Files with wildcards
    </td>
    <td>
      <sup>

```python
with f:
  f.index_files(['/tmp/*.mp4', '/tmp/*.pdf'])
```

</sup>
  </td>
<td>

Each file captured is constructed as a `Document`, and Document content (`text`, `blob`, `buffer`) is auto-guessed & filled.

</td>
</tr>

</table>

### Fetch Result
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-fetch-result.ipynb)

Once a request is done, callback functions are fired. Jina Flow implements a Promise-like interface: You can add callback functions `on_done`, `on_error`, `on_always` to hook different events. In the example below, our Flow passes the message then prints the result when successful. If something goes wrong, it beeps. Finally, the result is written to `output.txt`.

```python
def beep(*args):
    # make a beep sound
    import os
    os.system('echo -n "\a";')

with Flow().add() as f, open('output.txt', 'w') as fp:
    f.index(numpy.random.random([4, 5, 2]),
            on_done=print, on_error=beep, on_always=lambda x: fp.write(x.json()))
```

### Add Logic
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-add-logic.ipynb)

To add logic to the Flow, use the `uses` parameter to attach a Pod with an [Executor](https://101.jina.ai/#executor). `uses` accepts multiple value types including class name, Docker image, (inline) YAML or built-in shortcut.


```python
f = (Flow().add(uses=MyBertEncoder)  # the class of a Jina Executor
           .add(uses='docker://jinahub/pod.encoder.dummy_mwu_encoder:0.0.6-0.9.3')  # the image name
           .add(uses='myencoder.yml')  # YAML serialization of a Jina Executor
           .add(uses='!WaveletTransformer | {freq: 20}')  # inline YAML config
           .add(uses='_pass')  # built-in shortcut executor
           .add(uses={'__cls': 'MyBertEncoder', 'with': {'param': 1.23}}))  # dict config object with __cls keyword
```

The power of Jina lies in its decentralized architecture: Each `add` creates a new Pod, and these Pods can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote Docker container.

### Inter & Intra Parallelism
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-inter-intra-parallelism.ipynb)

Chaining `.add()`s creates a sequential Flow. For parallelism, use the `needs` parameter:

```python
f = (Flow().add(name='p1', needs='gateway')
           .add(name='p2', needs='gateway')
           .add(name='p3', needs='gateway')
           .needs(['p1','p2', 'p3'], name='r1').plot())
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-plot3.svg?raw=true"/>

`p1`, `p2`, `p3` now subscribe to `Gateway` and conduct their work in parallel. The last `.needs()` blocks all Pods until they finish their work. Note: parallelism can also be performed inside a Pod using `parallel`:

```python
f = (Flow().add(name='p1', needs='gateway')
           .add(name='p2', needs='gateway')
           .add(name='p3', parallel=3)
           .needs(['p1','p3'], name='r1').plot())
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-plot4.svg?raw=true"/>

### Decentralized Flow
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/decentralized-flow.ipynb)

A Flow does not have to be local-only: You can put any Pod to remote(s). In the example below, with the `host` keyword `gpu-pod`, is put to a remote machine for parallelization, whereas other Pods stay local. Extra file dependencies that need to be uploaded are specified via the `upload_files` keyword.

<table>
    <tr>
    <td>123.456.78.9</td>
    <td>

```bash
# have docker installed
docker run --name=jinad --network=host -v /var/run/docker.sock:/var/run/docker.sock jinaai/jina:latest-daemon --port-expose 8000
 to stop it
docker rm -f jinad
```

</td>
</tr>
  <tr>
    <td>
    Local
    </td>
    <td>

```python
import numpy as np
from jina import Flow

f = (Flow()
     .add()
     .add(name='gpu_pod',
          uses='mwu_encoder.yml',
          host='123.456.78.9:8000',
          parallel=2,
          upload_files=['mwu_encoder.py'])
     .add())

with f:
    f.index_ndarray(np.random.random([10, 100]), output=print)
```
</tr>

</table>

We provide a demo server on `cloud.jina.ai:8000`, give the following snippet a try!

```python
from jina import Flow

with Flow().add().add(host='cloud.jina.ai:8000') as f:
    f.index(['hello', 'world'])
```

### Asynchronous Flow
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-inter-intra-parallelism.ipynb)

While synchronous from outside, Jina runs asynchronously under the hood: it manages the eventloop(s) for scheduling the jobs. If the user wants more control over the eventloop, then `AsyncFlow` can be used.

Unlike `Flow`, the CRUD of `AsyncFlow` accepts input and output functions as [async generators](https://www.python.org/dev/peps/pep-0525/). This is useful when your data sources involve other asynchronous libraries (e.g. motor for MongoDB):

```python
from jina import AsyncFlow

async def input_function():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)

with AsyncFlow().add() as f:
    async for resp in f.index(input_function):
        print(resp)
```

`AsyncFlow` is particularly useful when Jina is using as part of integration, where another heavy-lifting job is running concurrently:

```python
async def run_async_flow_5s():  # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow().add(uses='- !WaitDriver {}') as f:
        async for resp in f.index_ndarray(numpy.random.random([5, 4])):
            print(resp)

async def heavylifting():  # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')

async def concurrent_main():  # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(), heavylifting())

if __name__ == '__main__':
    asyncio.run(concurrent_main())
```

`AsyncFlow` is very useful when using Jina inside a Jupyter Notebook. As Jupyter/ipython already manages an eventloop and thanks to [`autoawait`](https://ipython.readthedocs.io/en/stable/interactive/autoawait.html), `AsyncFlow` can run out-of-the-box in Jupyter.

That's all you need to know for understanding the magic behind `hello-world`. Now let's dive deeper into it!

---

|     |   |
| --- |---|
| 🥚  | [CRUD Functions](#crud-functions) • [Document](#document) • [Flow](#flow)  |
| 🐣  | [Feed Data](#feed-data) • [Fetch Result](#fetch-result) • [Add Logic](#add-logic) • [Inter & Intra Parallelism](#inter--intra-parallelism) • [Decentralize](#decentralized-flow) • [Asynchronous](#asynchronous-flow) |
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [Flow Optimization](#flow-optimization) • [REST Interface](#rest-interface) |

## 🐥 Breakdown of `hello-world`

### Customize Encoder

Let's first build a naive image encoder that embeds images into vectors using an orthogonal projection. To do this, we simply inherit from `BaseImageEncoder`: a base class from the `jina.executors.encoders` module. We then override its `__init__()` and `encode()` methods.


```python
import numpy as np
from jina.executors.encoders import BaseImageEncoder

class MyEncoder(BaseImageEncoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        np.random.seed(1337)
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    def encode(self, data: 'np.ndarray', *args, **kwargs):
        return (data.reshape([-1, 784]) / 255) @ self.oth_mat
```

Jina provides [a family of `Executor` classes](https://101.jina.ai/#executor), which summarize frequently-used algorithmic components in neural search. This family consists of encoders, indexers, crafters, evaluators, and classifiers, each with a well-designed interface. You can find the list of [all 107 built-in executors here](https://docs.jina.ai/chapters/all_exec.html). If they don't meet your needs, inheriting from one of them is the easiest way to bootstrap your own Executor. Simply use our Jina Hub CLI:


```bash
pip install jina[hub] && jina hub new
```

### Test Encoder in Flow

Let's test our encoder in the Flow with some synthetic data:


```python
def validate(req):
    assert len(req.docs) == 100
    assert NdArray(req.docs[0].embedding).value.shape == (64,)

f = Flow().add(uses='MyEncoder')

with f:
    f.index_ndarray(numpy.random.random([100, 28, 28]), on_done=validate)
```


All good! Now our `validate` function confirms that all one hundred 28x28 synthetic images have been embedded into 100x64 vectors.

### Parallelism & Batching

By setting a larger input, you can play with `batch_size` and `parallel`:


```python
f = Flow().add(uses='MyEncoder', parallel=10)

with f:
    f.index_ndarray(numpy.random.random([60000, 28, 28]), batch_size=1024)
```

### Add Data Indexer

Now we need to add an indexer to store all the embeddings and the image for later retrieval. Jina provides a simple `numpy`-powered vector indexer `NumpyIndexer`, and a key-value indexer `BinaryPbIndexer`. We can combine them in a single YAML file:

```yaml
jtype: CompoundIndexer
components:
  - jtype: NumpyIndexer
    with:
      index_filename: vec.gz
  - jtype: BinaryPbIndexer
    with:
      index_filename: chunk.gz
metas:
  workspace: ./
```

- `jtype:` defines the class name of the structure;
- `with:` defines arguments for initializing this class object.

[💡 Config your IDE to enable autocompletion on YAML](#yaml-completion-in-ide)

Essentially, the above YAML config is equivalent to the following Python code:

```python
from jina.executors.indexers.vector import NumpyIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers import CompoundIndexer

a = NumpyIndexer(index_filename='vec.gz')
b = BinaryPbIndexer(index_filename='vec.gz')
c = CompoundIndexer()
c.components = lambda: [a, b]
```

### Compose Flow from YAML

Now let's add our indexer YAML file to the Flow with `.add(uses=)`. Let's also add two shards to the indexer to improve its scalability:

```python
f = Flow().add(uses='MyEncoder', parallel=2).add(uses='myindexer.yml', shards=2).plot()
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-flow1.svg?raw=true"/>

When you have many arguments, constructing a Flow in Python can get cumbersome. In that case, you can simply move all arguments into one `flow.yml`:

```yaml
jtype: Flow
version: '1.0'
pods:
  - name: encode
    uses: MyEncoder
    parallel: 2
  - name:index
    uses: myindexer.yml
    shards: 2
```

And then load it in Python:

```python
f = Flow.load_config('flow.yml')
```

### Search

Querying a Flow is similar to what we did with indexing. Simply load the query Flow and switch from `f.index` to `f.search`. Say you want to retrieve the top 50 documents that are similar to your query and then plot them in HTML:


```python
f = Flow.load_config('flows/query.yml')
with f:
    f.search_ndarray(numpy.random.random([10, 28, 28]), shuffle=True, on_done=plot_in_html, top_k=50)
```

### Evaluation

To compute precision recall on the retrieved result, you can add `_eval_pr`, a built-in evaluator for computing precision & recall.

```python
f = (Flow().add(...)
           .add(uses='_eval_pr'))
```

You can construct an iterator of query and groundtruth pairs and feed to the flow `f`, via:

```python
from jina import Document

def query_generator():
    for _ in range(10):
        q = Document()
        # now construct expect matches as groundtruth
        gt = Document(q, copy=True)  # make sure 'gt' is identical to 'q'
        gt.matches.append(...)
        yield q, gt

f.search(query_iterator, ...)
```


#### Flow Optimization
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jupyter-notebooks/blob/main/basic-optimizer/basic-optimizer.ipynb)


Flow Optimization gets the most out of your data.
It allows hyper parameter optimization on a complete search Flow, including indexing and querying.
For example, choosing a middle layer of a model often results in richer semantic embeddings.
Let's test through all layers of a model.

Before starting, we need the optimizer requirements installed:

```bash
pip install jina[optimizer]
```

First, let's get all needed imports and the Flow definition:

```python
import numpy as np
from jina import Document
from jina.executors.encoders import BaseEncoder
from jina.optimizers import FlowOptimizer, MeanEvaluationCallback
from jina.optimizers.flow_runner import SingleFlowRunner

flow = '''jtype: Flow
version: '1'
pods:
  - uses:
      jtype: SimpleEncoder
      with:
        layer: ${{JINA_ENCODER_LAYER}}
  - uses: EuclideanEvaluator
'''
```

`ENCODER_LAYER` allows the optimizer to change the Encoder configuration with each iteration.
The `EuclideanEvaluator` scores the Documents according to a given groundtruth.
Beware, that the Pod definition is done via the inline syntax of Jina.

Now we will fake a model with three layers.
For simplicity each layer only consists of a single integer which is taken as the embedding.

```python
class SimpleEncoder(BaseEncoder):

    ENCODE_LOOKUP = {
        '🐲': [1, 3, 5],
        '🐦': [2, 4, 7],
        '🐢': [0, 2, 5],
    }

    def __init__(self, layer=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._layer = layer

    def encode(self, data, *args, **kwargs) -> 'np.ndarray':
        return np.array([[self.ENCODE_LOOKUP[data[0]][self._layer]]])
```

Futhermore, we define what should be the optimization parameters in `parameter.yml`.

```yaml
- !IntegerParameter
  jaml_variable: JINA_ENCODER_LAYER
  high: 2
  low: 0
  step_size: 1
```

For optimization, we need to run almost equal Flows again and again with the same data.
This is realized with a `SingleFlowRunner`.

```python
documents = [
    (Document(content='🐲'), Document(embedding=np.array([2]))),
    (Document(content='🐦'), Document(embedding=np.array([3]))),
    (Document(content='🐢'), Document(embedding=np.array([3])))
]

runner = SingleFlowRunner(
    flow, documents, 1, 'search', overwrite_workspace=True
)
```

The same Documents are used for each Flow Optimization step.
`documents` consists of `document, groundtruth` pairs.
The given embedding represents the perfect semantic embedding.

Now we are ready to start the optimization:

```python
optimizer = FlowOptimizer(
    flow_runner=runner,
    parameter_yaml='parameter.yml',
    evaluation_callback=MeanEvaluationCallback(),
    n_trials=3,
    direction='minimize',
    seed=1
)

optimizer.optimize_flow()
```

The `MeanEvaluationCallback` gathers the evaluations from all three sended Documents per run.
After each run, it returns the mean of the single evaluations.

Finally...

```text
...
JINA@15892[I] Trial 2 finished with value: 1.6666666666666667
and parameters: {'JINA_ENCODER_LAYER': 0}.
Best is trial 0 with value: 1.0.
JINA@15892[I]:Number of finished trials: 3
JINA@15892[I]:Best trial: {'JINA_ENCODER_LAYER': 1}
JINA@15892[I]:Time to finish: 0:00:02.081710

```

Tada! The layer 1 is the best one.

For a more detailed guide please read [our docs](https://docs.jina.ai/chapters/optimization/?highlight=optimization).

### REST Interface

In practice, the query Flow and the client (i.e. data sender) are often physically separated. Moreover, the client may prefer to use a REST API rather than gRPC when querying. You can set `port_expose` to a public port and turn on [REST support](https://api.jina.ai/rest/) with `restful=True`:

```python
f = Flow(port_expose=45678, restful=True)

with f:
    f.block()
```


That is the essence behind `jina hello fashion`. It is merely a taste of what Jina can do. We’re really excited to see what you do with Jina! You can easily create a Jina project from templates with one terminal command:

```bash
pip install jina[hub] && jina hub new --type app
```

This creates a Python entrypoint, YAML configs and a Dockerfile. You can start from there.

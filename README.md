<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina banner" width="200px">
</p>
<p align="center">
An easier way to build neural search on the cloud
</p>
<p align=center>
<a href="#license"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true" alt="Jina" title="Jina is licensed under Apache-2.0"></a>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://github.com/jina-ai/jina/actions?query=workflow%3ACI"><img src="https://github.com/jina-ai/jina/workflows/CI/badge.svg" alt="CI"></a>
<a href="https://github.com/jina-ai/jina/actions?query=workflow%3ACD"><img src="https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master" alt="CD"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img src="https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg" alt="codecov"></a>
</p>


Jina is a deep learning-powered search framework for building <strong>cross-/multi-modal search systems</strong> (e.g. text, images, video, audio) on the cloud.

⏱️ **Time Saver** - *The* design pattern of neural search systems, from zero to a production-ready system in minutes.

🍱 **Full-Stack Ownership** - Keep an end-to-end stack ownership of your solution, avoid the integration pitfalls with fragmented, multi-vendor, generic legacy tools.

🌌 **Universal Search** - Large-scale indexing and querying of unstructured data: video, image, long/short text, music, source code, etc.

🧠 **First-Class AI Models** - First-class support for [state-of-the-art AI models](https://docs.jina.ai/chapters/all_exec.html), easily usable and extendable with a Pythonic interface.

🌩️ **Fast & Cloud Ready** - Decentralized architecture from day one. Scalable & cloud-native by design: enjoy containerizing, distributing, sharding, async, REST/gRPC/WebSocket.

❤️  **Made with Love** - Never compromise on quality, actively maintained by a [passionate full-time, venture-backed team](https://jina.ai).

---

<p align="center">
<a href="http://docs.jina.ai">Docs</a> • <a href="#jina-hello-world-">Hello World</a> • <a href="#get-started">Quick Start</a> • <a href="#learn">Learn</a> • <a href="https://github.com/jina-ai/examples">Examples</a> • <a href="#contributing">Contribute</a> • <a href="https://jobs.jina.ai">Jobs</a> • <a href="http://jina.ai">Website</a> • <a href="http://slack.jina.ai">Slack</a>
</p>


## Installation

| 📦<br><sub><sup>x86/64,arm/v6,v7,[v8 (Apple M1)](https://github.com/jina-ai/jina/issues/1781)</sup></sub> | On Linux/macOS & Python 3.7/3.8/[3.9](https://github.com/jina-ai/jina/issues/1801) | Docker Users|
| --- | --- | --- |
| Standard | `pip install -U jina` | `docker run jinaai/jina:latest` |
| <sub><a href="https://api.jina.ai/daemon/">Daemon</a></sub> | <sub>`pip install -U "jina[daemon]"`</sub> | <sub>`docker run --network=host jinaai/jina:latest-daemon`</sub> |
| <sub>With Extras</sub> | <sub>`pip install -U "jina[devel]"`</sub> | <sub>`docker run jinaai/jina:latest-devel`</sub> |
| <sub>Dev/Pre-Release</sub> | <sub>`pip install --pre jina`</sub> | <sub>`docker run jinaai/jina:master`</sub> |

Version identifiers [are explained here](https://github.com/jina-ai/jina/blob/master/RELEASE.md). To install Jina with extra dependencies [please refer to the docs](https://docs.jina.ai/chapters/install/via-pip.html). Jina can run on [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

### YAML Completion in IDE

Developing Jina app often means writing YAML configs. We provide a [JSON Schema](https://json-schema.org/) for your IDE to enable code completion, syntax validation, members listing and displaying help text. Here is a [video tutorial](https://youtu.be/qOD-6mihUzQ) to walk you through the setup.

<table>
  <tr>
    <td>
<a href="https://www.youtube.com/watch?v=qOD-6mihUzQ&ab_channel=JinaAI"><img src="https://github.com/jina-ai/jina/blob/master/.github/images/pycharm-schema.gif?raw=true" /></a>
    </td>
    <td>

**PyCharm**

1. Click menu `Preferences` -> `JSON Schema mappings`;
2. Add a new schema, in the `Schema File or URL` write `https://api.jina.ai/schemas/latest.json`; select `JSON Schema Version 7`;
3. Add a file path pattern and link it to `*.jaml` and `*.jina.yml`.

</td>
</tr>
<tr>
    <td>
<a href="https://www.youtube.com/watch?v=qOD-6mihUzQ&ab_channel=JinaAI"><img src="https://github.com/jina-ai/jina/blob/master/.github/images/vscode-schema.gif?raw=true" /></a>
    </td>
    <td>

**VSCode**

1. Install the extension: `YAML Language Support by Red Hat`;
2. In IDE-level `settings.json` add:

```json
"yaml.schemas": {
    "https://api.jina.ai/schemas/latest.json": ["/*.jina.yml", "/*.jaml"],
}
```

</td>
</tr>
</table>


## Jina "Hello, World!" 👋🌍

Just starting out? Try Jina's "Hello, World" - `jina hello --help`

### 👗 Fashion Image Search


<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world.gif?raw=true" />
</a>

A simple image neural search demo for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No extra dependencies needed, simply run:

```bash
jina hello fashion  # more options in --help
```

...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello fashion --workdir /j && open j/hello-world.html
# replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click here to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world-demo.png?raw=true" alt="hello world console output">
</p>


</details>
This downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set. Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results. The whole process takes about 1 minute.


### 🤖 Covid-19 Chatbot

<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-chatbot.gif?raw=true" />
</a>

For NLP engineers, we provide a simple chatbot demo for answering Covid-19 questions. To run that:
```bash
pip install "jina[chatbot]"

jina hello chatbot
```

This downloads [CovidQA dataset](https://www.kaggle.com/xhlulu/covidqa) and tells Jina to index 418 question-answer pairs with DistilBERT. The index process takes about 1 minute on CPU. Then it opens a web page where you can input questions and ask Jina.

<br><br>

### 🪆 Multimodal Document Search

<a href="https://youtu.be/B_nH8GCmBfc">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-multimodal.gif?raw=true" />
</a>

A multimodal-document contains multiple data types, e.g. a PDF document often contains figures and text. Jina lets you build a multimodal search solution in just minutes. To run our minimum multimodal document search demo:
```bash
pip install "jina[multimodal]"

jina hello multimodal
```

This downloads [people image dataset](https://www.kaggle.com/ahmadahmadzada/images2000) and tells Jina to index 2,000 image-caption pairs with MobileNet and DistilBERT. The index process takes about 3 minute on CPU. Then it opens a web page where you can query multimodal documents. We have prepared [a YouTube tutorial](https://youtu.be/B_nH8GCmBfc) to walk you through this demo.


<br><br><br>

## Get Started

|     |   |
| --- |---|
| 🥚  | [CRUD Functions](#crud-functions) • [Document](#document) • [Flow](#flow)  |
| 🐣  | [Feed Data](#feed-data) • [Fetch Result](#fetch-result) • [Add Logic](#add-logic) • [Inter & Intra Parallelism](#inter--intra-parallelism) • [Decentralize](#decentralized-flow) • [Asynchronous](#asynchronous-flow) |
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [REST Interface](#rest-interface) |

### 🥚 Fundamentals

#### CRUD Functions
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-basic-crud-functions.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

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


#### Document
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-construct-document.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

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


#### MultimodalDocument

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

##### Fusion Embeddings from Different Modalities

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

#### Flow
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-create-flow.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

Jina provides a high-level Flow API to simplify building CRUD workflows. To create a new Flow:

```python
from jina import Flow
f = Flow().add()
```

This creates a simple Flow with one [Pod](https://101.jina.ai/#pod). You can chain multiple `.add()`s in a single Flow.

<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-visualize-a-flow.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

To visualize the Flow, simply chain it with `.plot('my-flow.svg')`. If you are using a Jupyter notebook, the Flow object will be displayed inline *without* `plot`.

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-flow0.svg?raw=true"/>

`Gateway` is the entrypoint of the Flow.

Get the vibe? Now we're talking! Let's learn more about the basic concepts and features of Jina:

---

|     |   |
| --- |---|
| 🥚  | [CRUD Functions](#crud-functions) • [Document](#document) • [Flow](#flow)  |
| 🐣  | [Feed Data](#feed-data) • [Fetch Result](#fetch-result) • [Add Logic](#add-logic) • [Inter & Intra Parallelism](#inter--intra-parallelism) • [Decentralize](#decentralized-flow) • [Asynchronous](#asynchronous-flow) |
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [REST Interface](#rest-interface) |


### 🐣 Basic

#### Feed Data
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-feed-data.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

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
  f.index_csv(fp1, field_resolver={'pic_url': 'uri'})
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
  f.index_ndjson(fp1, field_resolver={'question_id': 'id'})
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

#### Fetch Result
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-fetch-result.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

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

#### Add Logic
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-add-logic.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

To add logic to the Flow, use the `uses` parameter to attach a Pod with an [Executor](https://101.jina.ai/#executor). `uses` accepts multiple value types including class name, Docker image, (inline) YAML or built-in shortcut.


```python
f = (Flow().add(uses='MyBertEncoder')  # class name of a Jina Executor
           .add(uses='docker://jinahub/pod.encoder.dummy_mwu_encoder:0.0.6-0.9.3')  # the image name
           .add(uses='myencoder.yml')  # YAML serialization of a Jina Executor
           .add(uses='!WaveletTransformer | {freq: 20}')  # inline YAML config
           .add(uses='_pass')  # built-in shortcut executor
           .add(uses={'__cls': 'MyBertEncoder', 'with': {'param': 1.23}}))  # dict config object with __cls keyword
```

The power of Jina lies in its decentralized architecture: Each `add` creates a new Pod, and these Pods can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote Docker container.

#### Inter & Intra Parallelism
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-inter-intra-parallelism.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

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

#### Decentralized Flow
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=decentralized-flow.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

A Flow does not have to be local-only: You can put any Pod to remote(s). In the example below, with the `host` keyword `gpu-pod`, is put to a remote machine for parallelization, whereas other Pods stay local. Extra file dependencies that need to be uploaded are specified via the `upload_files` keyword.

<table>
    <tr>
    <td>123.456.78.9</td>
    <td>

```bash
# have docker installed
docker run --name=jinad --network=host -v /var/run/docker.sock:/var/run/docker.sock jinaai/jina:latest-daemon --port-expose 8000
# to stop it
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

#### Asynchronous Flow
<a href="https://mybinder.org/v2/gh/jina-ai/jupyter-notebooks/main?filepath=basic-inter-intra-parallelism.ipynb"><img align="right" src="https://github.com/jina-ai/jina/blob/master/.github/badges/run-badge.svg?raw=true"/></a>

While synchronous from outside, Jina runs asynchronously under the hood: it manages the eventloop(s) for scheduling the jobs. If the user wants more control over the eventloop, then `AsyncFlow` can be used.

Unlike `Flow`, the CRUD of `AsyncFlow` accepts input and output functions as [async generators](https://www.python.org/dev/peps/pep-0525/). This is useful when your data sources involve other asynchronous libraries (e.g. motor for MongoDB):

```python
from jina import AsyncFlow

async def input_fn():
    for _ in range(10):
        yield Document()
        await asyncio.sleep(0.1)

with AsyncFlow().add() as f:
    async for resp in f.index(input_fn):
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
| 🐥 | [Customize Encoder](#customize-encoder) • [Test Encoder](#test-encoder-in-flow) • [Parallelism & Batching](#parallelism--batching) • [Add Data Indexer](#add-data-indexer) • [Compose Flow from YAML](#compose-flow-from-yaml) • [Search](#search) • [Evaluation](#evaluation) • [REST Interface](#rest-interface) |

### 🐥 Breakdown of `hello-world`

#### Customize Encoder

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

#### Test Encoder in Flow

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

#### Parallelism & Batching

By setting a larger input, you can play with `batch_size` and `parallel`:


```python
f = Flow().add(uses='MyEncoder', parallel=10)

with f:
    f.index_ndarray(numpy.random.random([60000, 28, 28]), batch_size=1024)
```

#### Add Data Indexer

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

#### Compose Flow from YAML

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

#### Search

Querying a Flow is similar to what we did with indexing. Simply load the query Flow and switch from `f.index` to `f.search`. Say you want to retrieve the top 50 documents that are similar to your query and then plot them in HTML:


```python
f = Flow.load_config('flows/query.yml')
with f:
    f.search_ndarray(numpy.random.random([10, 28, 28]), shuffle=True, on_done=plot_in_html, top_k=50)
```

#### Evaluation

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


#### REST Interface

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

## Learn

<table>
  <tr>
    <td width="25%">
    <a href="https://101.jina.ai">
      <img src="https://github.com/jina-ai/jina/blob/master/.github/images/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="75%">
&nbsp;&nbsp;<h3><a href="https://101.jina.ai">Jina 101: First Things to Learn About Jina</a></h3>
    </td>

  </tr>
</table>

### Examples ([View all](https://github.com/jina-ai/examples))

Example code to build your own projects

<table>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/wikipedia-sentences">NLP Semantic Wikipedia Search with Transformers and DistilBERT</a></h4>
      Brand new to neural search? See a simple text-search example to understand how Jina works
    </td>
  </tr>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/wikipedia-sentences-incremental">Add Incremental Indexing to Wikipedia Search</a></h4>
      Index more effectively by adding incremental indexing to your Wikipedia search
    </td>
  </tr>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Search Lyrics with Transformers and PyTorch</a></h4>
      Get a better understanding of chunks by searching a lyrics database. Now with shiny front-end!
    </td>
  </tr>
  <tr>
    <td>
      <h1>🖼️</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Google's Big Transfer Model in (Poké-)Production</a></h4>
      Use SOTA visual representation for searching Pokémon!
    </td>
  </tr>
  <tr>
    <td>
      <h1>🎧</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/audio-search">Search YouTube audio data with Vggish</a></h4>
      A demo of neural search for audio data based Vggish model.
    </td>
  </tr>
  <tr>
    <td>
      <h1>🎞️ </h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Search Tumblr GIFs with KerasEncoder</a></h4>
      Use prefetching and sharding to improve the performance of your index and query Flow when searching animated GIFs.
    </td>
  </tr>
</table>

Please check our [examples repo](https://github.com/jina-ai/examples) for advanced and community-submitted examples.

Want to read more? Check our Founder [Han Xiao's blog](https://hanxiao.io) and [our official blog](https://jina.ai/blog).

## Documentation

<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

Apart from the learning resources above, We highly recommended you go through our [**documentation**](https://docs.jina.ai) to master Jina.


Our docs are built on every push, merge, and release of Jina's master branch. Documentation for older versions is archived [here](https://github.com/jina-ai/docs/releases).

Are you a "Doc"-star? Join us! We welcome all kinds of improvements on the documentation.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to your active involvement.

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

### Contributors ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-120-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/carlosbaezruiz/"><img src="https://avatars.githubusercontent.com/u/1107703?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/deepampatel"><img src="https://avatars.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/lucia-loher/"><img src="https://avatars.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://hargup.in/"><img src="https://avatars.githubusercontent.com/u/2477788?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/prabhupad-pradhan/"><img src="https://avatars.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://jina.ai/"><img src="https://avatars.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/umbertogriffo"><img src="https://avatars.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Roshanjossey"><img src="https://avatars.githubusercontent.com/u/8488446?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/anshulwadhawan"><img src="https://avatars.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ThePfarrer"><img src="https://avatars.githubusercontent.com/u/7157861?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/SirsikarAkshay"><img src="https://avatars.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/janandreschweiger"><img src="https://avatars.githubusercontent.com/u/44372046?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/pgiank28"><img src="https://avatars.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/LukeekuL"><img src="https://avatars.githubusercontent.com/u/24293913?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.imxiqi.com/"><img src="https://avatars.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/jyothishkjames"><img src="https://avatars.githubusercontent.com/u/937528?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rjgallego"><img src="https://avatars.githubusercontent.com/u/59635994?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/clennan"><img src="https://avatars.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/FionnD"><img src="https://avatars.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/xinbinhuang"><img src="https://avatars.githubusercontent.com/u/27927454?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ManudattaG"><img src="https://avatars.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ApurvaMisra"><img src="https://avatars.githubusercontent.com/u/22544948?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/kaushikb11"><img src="https://avatars.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/samjoy"><img src="https://avatars.githubusercontent.com/u/3750744?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/uvipen"><img src="https://avatars.githubusercontent.com/u/47221207?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/harry-stark"><img src="https://avatars.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://sebastianlettner.info/"><img src="https://avatars.githubusercontent.com/u/51201318?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/doomdabo"><img src="https://avatars.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bio-howard"><img src="https://avatars.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://cristianmtr.github.io/resume/"><img src="https://avatars.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://www.efho.de/"><img src="https://avatars.githubusercontent.com/u/6096895?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/tadejsv"><img src="https://avatars.githubusercontent.com/u/11489772?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/serge-m"><img src="https://avatars.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/HelioStrike"><img src="https://avatars.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/averkij"><img src="https://avatars.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://bit.ly/3qKM0uO"><img src="https://avatars.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/BastinJafari"><img src="https://avatars.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/aga11313"><img src="https://avatars.githubusercontent.com/u/23415764?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/seraco"><img src="https://avatars.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://kilsenp.github.io/"><img src="https://avatars.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/pswu11"><img src="https://avatars.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/smy0428"><img src="https://avatars.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/akurniawan25/"><img src="https://avatars.githubusercontent.com/u/4723643?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Yongxuanzhang"><img src="https://avatars.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/yuanb/"><img src="https://avatars.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/yk"><img src="https://avatars.githubusercontent.com/u/858040?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tadej-redstone"><img src="https://avatars.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/PabloRN"><img src="https://avatars.githubusercontent.com/u/727564?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/PietroAnsidei"><img src="https://avatars.githubusercontent.com/u/31099206?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/NouiliKh"><img src="https://avatars.githubusercontent.com/u/22430520?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/hongchhe"><img src="https://avatars.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/davidbp"><img src="https://avatars.githubusercontent.com/u/4223580?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://prasakis.com/"><img src="https://avatars.githubusercontent.com/u/10392953?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Immich"><img src="https://avatars.githubusercontent.com/u/9353470?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fernandakawasaki"><img src="https://avatars.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fayeah"><img src="https://avatars.githubusercontent.com/u/29644978?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://blog.lsgrep.com/"><img src="https://avatars.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="32px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Community

- [Code of conduct](https://github.com/jina-ai/jina/blob/master/.github/CODE_OF_CONDUCT.md) - play nicely with the Jina community
- [Slack workspace](https://slack.jina.ai) - join #general on our Slack to meet the team and ask questions
- [YouTube channel](https://youtube.com/c/jina-ai) - subscribe to the latest video tutorials, release demos, webinars and presentations.
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - get to know Jina AI as a company and find job opportunities
- [![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - follow and interact with us using hashtag `#JinaSearch`
- [Company](https://jina.ai) - know more about our company and how we are fully committed to open-source.

## Open Governance

<a href="https://www.youtube.com/c/jina-ai">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/eah-god.png?raw=true " />
</a>

As part of our open governance model, we host Jina's [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) in public. This Zoom meeting recurs monthly on the second Tuesday of each month, at 14:00-15:30 (CET). Everyone can join in via the following calendar invite.

- [Add to Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Download .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

The meeting will also be live-streamed and later published to our [YouTube channel](https://youtube.com/c/jina-ai).

## Join Us

Jina is an open-source project. [We are hiring](https://jobs.jina.ai) full-stack developers, evangelists, and PMs to build the next neural search ecosystem in open source.


## License

Copyright (c) 2020-2021 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [See LICENSE for the full license text.](LICENSE)

<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina banner" width="200px">
</p>
<p align="center">
An easier way to build neural search in the cloud
</p>
<p align=center>
<a href="#license"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true" alt="Jina" title="Jina is licensed under Apache-2.0"></a>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://github.com/jina-ai/jina/actions?query=workflow%3ACI"><img src="https://github.com/jina-ai/jina/workflows/CI/badge.svg" alt="CI"></a>
<a href="https://github.com/jina-ai/jina/actions?query=workflow%3ACD"><img src="https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master" alt="CD"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img src="https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg" alt="codecov"></a>
<br>
<sub>
  <a href="https://github.com/jina-ai/jina">English</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.kr.md">한국어</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">український</a>
</sub>
</p>


Jina is a deep learning-powered search framework for building <strong>cross-/multi-modal search systems</strong> (e.g. text, images, video, audio) in the cloud. 

⏱️ **Time Saver** - Bootstrap an AI-powered system in just a few minutes.

🧠 **First-Class AI Models** - *The* design pattern for neural search systems, with first-class support for [state-of-the-art AI models](https://docs.jina.ai/chapters/all_exec.html).

🌌 **Universal Search** - Large-scale indexing and querying of any kind of data on multiple platforms: video, image, long/short text, music, source code, etc.

☁️  **Cloud Ready** - Decentralized architecture with cloud-native features out-of-the-box: containerization, microservice, scaling, sharding, async IO, REST, gRPC.

🧩 **Plug & Play** - Easily extendable with Pythonic interface.

❤️  **Made with Love** - Quality first, never compromises, maintained by a [full-time, venture-backed team](https://jina.ai).

---

<p align="center">
<a href="#jina-hello-world-">Hello World</a> • <a href="#get-started">Quick Start</a> • <a href="#learn">Learn</a> • <a href="#contributing">Contribute</a> • <a href="https://jobs.jina.ai">Jobs</a> • <a href="http://jina.ai">Website</a> • <a href="http://slack.jina.ai">Slack</a>
</p>


## Installation

On Linux/macOS with Python 3.7/3.8:

```bash
pip install -U jina
```

To install Jina with extra dependencies, or install on Raspberry Pi [please refer to the documentation](https://docs.jina.ai/chapters/install/via-pip.html). Windows users can use Jina via the [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

#### In a Docker Container

Our universal Docker image supports multiple architectures (including x64, x86, arm-64/v7/v6). They are ready-to-use:

```bash
docker run jinaai/jina --help
```

## Jina "Hello, World!" 👋🌍

Just starting out? Try Jina's "Hello, World" - a simple image neural search demo for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No extra dependencies needed, simply run:

```bash
jina hello-world
```

...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  
# replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click here to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>
This downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set. Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results. The whole process takes about 1 minute, and after running opens a webpage and shows results:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="80%">
</p>

Intrigued? Play with different options:

```bash
jina hello-world --help
```

## Get Started

#### Create

Jina provides a high-level [Flow API](https://github.com/jina-ai/jina/tree/master/docs/chapters/101#flow) to simplify building search/index workflows. To create a new Flow:

```python
from jina import Flow
f = Flow().add()
```

This creates a simple Flow with one [Pod](https://github.com/jina-ai/jina/tree/master/docs/chapters/101#pods). You can chain multiple `.add()`s in a single Flow.

#### Visualize

To visualize the Flow, simply chain it with `.plot('my-flow.svg')`. If you are using a Jupyter notebook, it's even easier:

```python
f
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-flow0.svg?raw=true"/>

`Gateway` is the entrypoint of the Flow. 

#### Feed Data

Let's create some random data and index it:

```python
from jina import Document

with Flow().add() as f:
    f.index_ndarray(numpy.random.random([4,2]), output_fn=print)  # index ndarray data, document sliced on first dimension
    f.index_lines(['hello world!', 'goodbye world!'])  # index textual data, each element is a document
    f.index_files(['/tmp/*.mp4', '/tmp/*.pdf'])  # index files and wildcard globs, each file is a document
    f.index((Document() for _ in range(10)))  # index raw Jina Documents
```

To use a Flow, open it using the `with` context manager, like you would a file in Python. You can call `index` and `search` with nearly all types of data. The whole data stream is asynchronous and efficient.

#### Fetch Result

Once a request is done, callback functions are fired. Jina Flow implements Promise-like interface, you can add callback functions `on_error`, `on_always` to hook different event. In the example below, our Flow passes the message then prints the result when success. If something wrong, it beeps. Finally, the result is written to `output.txt`.

```python
def beep(*args):
    # make a beep sound
    import os
    os.system('echo -n "\a";')

with Flow().add() as f, open('output.txt', 'w') as fp:
    f.index(numpy.random.random([4,5,2]),
            output_fn=print,
            on_error=beep, on_always=fp.write)
```

#### Add Logic

To add logic to the Flow, use the `uses` parameter to attach a Pod with an [Executor](https://github.com/jina-ai/jina/tree/master/docs/chapters/101#executors). `uses` accepts multiple value types including class name, Docker image, (inline) YAML or built-in shortcut.


```python
f = (Flow().add(uses='MyBertEncoder')  # class name of a Jina Executor
           .add(uses='jinahub/pretrained-cnn:latest')  # Dockerized Jina Pod
           .add(uses='myencoder.yaml')  # YAML serialization of a Jina Executor
           .add(uses='!WaveletTransformer | {freq: 20}')  # inline YAML config
           .add(uses='_pass'))  # built-in shortcut executor
```

The power of Jina lies in its decentralized architecture: each `add` creates a new Pod, and these Pods can be run as a local thread/process, a remote process, inside a Docker container, or even inside a remote Docker container.

#### Inter & Intra Parallelism

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

#### Asynchronous Flow

Synchronous from outside, Jina runs asynchronously underneath: it manages the eventloop(s) for scheduling the jobs. In some scenario, user wants more control over the eventloop, then `AsyncFlow` comes to use. In the example below, Jina is part of the integration where another heavy-lifting job is running concurrently:

```python
from jina import AsyncFlow

async def run_async_flow_5s():  # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow().add(uses='- !WaitDriver {}') as f:
        await f.index_ndarray(np.random.random([5, 4]), output_fn=validate)

async def heavylifting():  # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')

async def concurrent_main():  # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(), heavylifting())

if __name__ == '__main__':
    asyncio.run(concurrent_main())
```

`AsyncFlow` is very useful when using Jina inside Jupyter Notebook. As Jupyter/ipython already manages an eventloop and thanks to [`autoawait`](https://ipython.readthedocs.io/en/stable/interactive/autoawait.html), the following code can run out-of-the-box in Jupyter:

```python
from jina import AsyncFlow

with AsyncFlow().add() as f:
    await f.index_ndarray(np.random.random([5, 4]), output_fn=print)
```


That's all you need to know for understanding the magic behind `hello-world`. Now let's dive into it!

### Breakdown of `hello-world`

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

Jina provides [a family of `Executor` classes](https://github.com/jina-ai/jina/tree/master/docs/chapters/101#the-executor-family), which summarize frequently-used algorithmic components in neural search. This family consists of encoders, indexers, crafters, evaluators, and classifiers, each with a well-designed interface. You can find the list of [all 107 built-in executors here](https://docs.jina.ai/chapters/all_exec.html). If they don't meet your needs, inheriting from one of them is the easiest way to bootstrap your own Executor. Simply use our Jina Hub CLI:


```bash
pip install jina[hub] && jina hub new
```

#### Test Encoder in Flow

Let's test our encoder in the Flow with some synthetic data:


```python
def validate(docs):
    assert len(docs) == 100
    assert NdArray(docs[0].embedding).value.shape == (64,)

f = Flow().add(uses='MyEncoder')

with f:
    f.index_ndarray(np.random.random([100, 28, 28]), output_fn=validate, callback_on='docs')
```


All good! Now our `validate` function confirms that all one hundred 28x28 synthetic images have been embedded into 100x64 vectors. 

#### Parallelism & Batching

By setting a larger input, you can play with `batch_size` and `parallel`:


```python
f = Flow().add(uses='MyEncoder', parallel=10)

with f:
    f.index_ndarray(np.random.random([60000, 28, 28]), batch_size=1024)
```

#### Add Data Indexer

Now we need to add an indexer to store all the embeddings and the image for later retrieval. Jina provides a simple `numpy`-powered vector indexer `NumpyIndexer`, and a key-value indexer `BinaryPbIndexer`. We can combine them in a single YAML file:

```yaml
!CompoundIndexer
components:
  - !NumpyIndexer
    with:
      index_filename: vec.gz
  - !BinaryPbIndexer
    with:
      index_filename: chunk.gz
metas:
  workspace: ./
```

- `!` tags a structure with a class name
- `with` defines arguments for initializing this class object.
 
Essentially, the above YAML config is equivalent to the following Python code:

```python
from jina.executors.indexers.vector import NumpyIndexer
from jina.exeuctors.indexers.keyvalue import BinaryPbIndexer

a = NumpyIndexer(index_filename='vec.gz')
b = BinaryPbIndexer(index_filename='vec.gz')
c = CompoundIndexer()
c.components = lambda: [a, b]
```

#### Compose Flow in Python/YAML

Now let's add our indexer YAML file to the Flow with `.add(uses=)`. Let's also add two shards to the indexer to improve its scalability:

```python
f = Flow().add(uses='MyEncoder', parallel=2).add(uses='myindexer.yml', shards=2, separated_workspace=True).plot()
```

<img src="https://github.com/jina-ai/jina/blob/master/.github/simple-flow1.svg?raw=true"/>

When you have many arguments, constructing a Flow in Python can get cumbersome. In that case, you can simply move all arguments into one `flow.yml`:

```yaml
!Flow
pods:
  encode:
    uses: MyEncoder
    parallel: 2
  index:
    uses: myindexer.yml
    shards: 2
    separated_workspace: true
```

And then load it in Python:

```python
f = Flow.load_config('flow.yml')
```

#### Search via Query Flow

Querying a Flow is similar to what we did with indexing. Simply load the query Flow and switch from `f.index` to `f.search`. Say you want to retrieve the top 50 documents that are similar to your query and then plot them in HTML:


```python
f = Flow.load_config('flows/query.yml')
with f:
    f.search_ndarray(shuffle=True, size=128, output_fn=plot_in_html, top_k=50)
```

#### REST Interface of Query Flow

In practice, the query Flow and the client (i.e. data sender) are often physically seperated. Moreover, the client may prefer to use a REST API rather than gRPC when querying. You can set `port_expose` to a public port and turn on [REST support](https://docs.jina.ai/chapters/restapi/index.html) with `rest_api=True`:

```python
f = Flow(port_expose=45678, rest_api=True)

with f:
    f.block()
```


That is the essense behind `jina hello-world`. It is merely a taste of what Jina can do. We’re really excited to see what you do with Jina! You can easily create a Jina project from templates with one terminal command:

```bash
pip install jina[hub] && jina hub new --type app
```

This creates a Python entrypoint, YAML configs and a Dockerfile. You can start from there.

## Learn

<table>
  <tr>
    <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/101/img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: First Things to Learn About Jina</a></h3>
&nbsp;&nbsp;<a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">English</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.pt.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ar.md">عربية</a>
    </td>

  </tr>
</table>

### Build Your Search App

Get started with neural search, inputs, outputs, and Flows

<table>
  <tr>
    <th width="5%"></th>
    <th width="47.5%">Tutorials</th> 
    <th width="47.5%">Readings</th>
  </tr>
  <tr>
    <td>🐣</td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">My First Search App</a></h4>
      Beginners tutorial: Search Star Trek script data
      <h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Image Search</a></h4>
      Image to image search Pokémon sprites with Google's BiT model
      <h4><a href="https://github.com/jina-ai/examples/tree/master/audio-search">Audio Search</a></h4>
      Audio to audio search with Vggish model
    </td>
    <td>
      <h4><a href="https://jina.ai/2020/07/06/What-is-Neural-Search-and-Why-Should-I-Care.html">What is Neural Search?</a></h4>
      What it is, how it works, and how it's different
      <h4><a href="https://hanxiao.io/2020/11/22/Primitive-Data-Types-in-Neural-Search-System/">Primitive Data Types in Neural Search System</a></h4>
      Construct your first `Document` in Jina
      <h4><a href="https://hanxiao.io/2020/08/02/Layer-of-Abstraction-when-Building-Tensorflow-for-Search/">Jina's Layers of Abstraction</a></h4>
      Why do we build Jina and for whom?
      <h4><a href="https://hanxiao.io/2020/10/19/A-Curated-List-of-Neural-Search-and-Jina-Framework-Designs/">Curated List of Neural Search and Jina</a></h4>
      Comprehensive round-up on Jina tech, concepts
    </td>
  <tr>
    <td>🐥</td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">Search with QueryLanguage</a></h4>
      Filter search results by category
      <h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">NLP Semantic Search with Transformers</a></h4>
      Dig into Flows and Pods
    </td>
    <td>
      <h4><a href="https://docs.jina.ai/chapters/flow/index.html">Flow API: Compose Your Jina Workflow</a></h4>
      With Python, YAML, or graphical Dashboard
      <h4><a href="https://docs.jina.ai/chapters/io/index.html">Input and Output Functions</a></h4>
      Data goes in, data comes out. Here's how
    </td>
  </tr>
</table>

### Level Up Your Search App

Client-server, scaling, containerization, Docker, and more

<table>
  <tr>
    <th width="5%"></th>
    <th width="47.5%">Tutorials</th> 
    <th width="47.5%">Readings</th>
  </tr>
  <tr>
    <td>🐥</td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/helloworld-in-cs">Client-Server Architecture</a></h4>
      Refactor hello-world into client-server architecture
      <h4><a href="https://github.com/jina-ai/examples/tree/master/flower-search">Scale Up and Speed Up</a></h4>
      Scale up Pods to speed up your search and add a customized executor
      <h4><a href="https://github.com/jina-ai/dashboard">Workflow Insights in Dashboard</a></h4>Log and monitor with Jina's graphical Dashboard
    </td>
    <td>
      <h4><a href="https://docs.jina.ai/chapters/remote/index.html">Distribute Your Workflow Remotely</a></h4>
      Run Pods remotely via console, Jina Gateway, or Flow API
      <h4><a href="https://docs.jina.ai/chapters/hub/index.html">Jina in Docker</a></h4>
      Build your Pod into a Docker image: How and why
    </td>
  </tr>
</table>

Want to read more? Check our Founder [Han Xiao's blog](https://hanxiao.io) and [our official blog](https://jina.ai/blog). 

<!-- 

<table>
<tr>
<th width="10%">Level</th>
<th width="90%">Tutorials</th>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">Build an NLP Semantic Search System</a></h4>
Search South Park scripts and practice with Flows and Pods
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">My First Jina App</a></h4>
Using cookiecutter for bootstrap a jina app
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">Fashion Search with Query Language</a></h4>
Spice up the Hello-World with Query Language
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Use Chunk to search Lyrics</a></h4>
Split documents in order to search on a finegrained level
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/cross-modal-search">Mix and Match images and captions</a></h4>
Search cross modal to get images from captions and vice versa
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Scale Up Video Semantic Search</a></h4>
Improve performance using prefetching and sharding
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/x-as-service">From BERT-as-Service to X-as-Service</a></h4>
Extract feature vector data using any deep learning representation
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Google's Big Transfer Model in (Poké-)Production</a></h4>
Search Pokemon with state-of-the-art visual representation
</td>
</tr>
 -->
</table>

## Documentation

Apart from the learning resources we provided above, We highly recommended you go through our [**documentation**](https://docs.jina.ai) to master Jina.

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

Our docs are built on every push, merge, and release of Jina's master branch. Documentation for older versions is archived [here](https://github.com/jina-ai/docs/releases).

<!--

#### The Basics

- [Use Flow API to Compose Your Search Workflow](https://docs.jina.ai/chapters/flow/index.html)
- [Input and Output Functions in Jina](https://docs.jina.ai/chapters/io/index.html)
- [Use Dashboard to Get Insight of Jina Workflow](https://github.com/jina-ai/dashboard)
- [Distribute Your Workflow Remotely](https://docs.jina.ai/chapters/remote/index.html)
- [Run Jina Pods via Docker Container](https://docs.jina.ai/chapters/hub/index.html)

#### Reference

- [Command line interface arguments](https://docs.jina.ai/chapters/cli/index.html)
- [Python API interface](https://docs.jina.ai/api/jina.html)
- [YAML syntax for Executor, Driver and Flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Protobuf schema](https://docs.jina.ai/chapters/proto/index.html)
- [Environment variables](https://docs.jina.ai/chapters/envs.html)
- ... [and more](https://docs.jina.ai/index.html)

-->



Are you a "Doc"-star? Join us! We welcome all kinds of improvements on the documentation.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to your active involvement.

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

### Contributors ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-96-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jyothishkjames"><img src="https://avatars0.githubusercontent.com/u/937528?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/FionnD"><img src="https://avatars0.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/anshulwadhawan"><img src="https://avatars2.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://bit.ly/2UdLNBf"><img src="https://avatars2.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars3.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/clennan"><img src="https://avatars3.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/umbertogriffo"><img src="https://avatars2.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/averkij"><img src="https://avatars0.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Yongxuanzhang"><img src="https://avatars2.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/yuanb/"><img src="https://avatars0.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://cristianmtr.github.io/resume/"><img src="https://avatars3.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/HelioStrike"><img src="https://avatars1.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/pswu11"><img src="https://avatars2.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.imxiqi.com/"><img src="https://avatars2.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars1.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars2.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/doomdabo"><img src="https://avatars1.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bio-howard"><img src="https://avatars3.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://blog.lsgrep.com/"><img src="https://avatars3.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars2.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/BastinJafari"><img src="https://avatars3.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/serge-m"><img src="https://avatars2.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/Showtim3"><img src="https://avatars3.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/smy0428"><img src="https://avatars3.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars1.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars0.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/hongchhe"><img src="https://avatars0.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/pgiank28"><img src="https://avatars3.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/harry-stark"><img src="https://avatars3.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ManudattaG"><img src="https://avatars2.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars1.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fernandakawasaki"><img src="https://avatars2.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/florian-hoenicke"><img src="https://avatars2.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/prabhupad-pradhan/"><img src="https://avatars3.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/seraco"><img src="https://avatars1.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars1.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars1.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tadej-redstone"><img src="https://avatars1.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/deepampatel"><img src="https://avatars3.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars1.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars0.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/SirsikarAkshay"><img src="https://avatars1.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/lusloher"><img src="https://avatars2.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://kilsenp.github.io/"><img src="https://avatars1.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars3.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars2.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars1.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="32px;"/></a></kbd>


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

[GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to Jina's future improvements.

As part of our open governance model, we host Jina's [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) in public. This Zoom meeting recurs monthly on the second Tuesday of each month, at 14:00-15:30 (CET). Everyone can join in via the following calendar invite.

- [Add to Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Download .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

The meeting will also be live-streamed and later published to our [YouTube channel](https://youtube.com/c/jina-ai).

## Join Us

Jina is an open-source project. [We are hiring](https://jobs.jina.ai) full-stack developers, evangelists, and PMs to build the next neural search ecosystem in open source.


## License

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [See LICENSE for the full license text.](LICENSE)

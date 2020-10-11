<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/1500x667new.gif?raw=true" alt="Jina banner" width="100%">
</p>

<p align="center">

[![Jina](https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true  "Jina is licensed under Apache-2.0")](#license)
[![Python 3.7 3.8](https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true  "Jina supports Python 3.7 and above")](https://pypi.org/project/jina/)
[![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/)
[![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina is multi-arch ready, can run on different architectures")](https://hub.docker.com/r/jinaai/jina/tags)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&label=Docker%20Image&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)
[![API Schema](https://github.com/jina-ai/jina/workflows/API%20Schema/badge.svg)](https://api.jina.ai/)
[![codecov](https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg)](https://codecov.io/gh/jina-ai/jina)

</p>

<p align="center">
  <a href="https://github.com/jina-ai/jina">English</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.zh.md">中文</a>
</p>


<p align="center">
  <a href="https://jina.ai">Website</a> •
  <a href="https://docs.jina.ai">Docs</a> •
  <a href="https://learn.jina.ai">Examples</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://dashboard.jina.ai">Dashboard (beta)</a> •
  <a href="https://github.com/jina-ai/jinabox.js/">Jinabox (beta)</a> •
  <a href="http://www.twitter.com/JinaAI_">Twitter</a> •
  <a href="https://jobs.jina.ai">We are Hiring</a>

</p>

Jina is an AI-powered search framework, empowering developers to create **cross-/multi-modal search systems** (e.g. text, images, video, audio) on the cloud. Jina is long-term supported by a [full-time, venture-backed team](https://jina.ai).

⏱️ **Time Saver** - Bootstrap an AI-powered system in just a few minutes.

🧠 **First-Class AI models** - Jina is a new design pattern for neural search systems with first-class support for [state-of-the-art AI models](https://docs.jina.ai/chapters/all_exec.html).

🌌 **Universal Search** - Large-scale indexing and querying data of any kind on multiple platforms. Video, image, long/short text, music, source code, and more.

🚀 **Production Ready** - Cloud-native features work out-of-the-box, e.g. containerization, microservice, distributing, scaling, sharding, async IO, REST, gRPC.

🧩 **Plug & Play** - With [Jina Hub](https://github.com/jina-ai/jina-hub), easily extend Jina with simple Python scripts or Docker images optimized for your search domain.

## Contents

<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/install.png?raw=true " />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Get Started](#get-started)
- [Jina "Hello, World!" 👋🌍](#jina-hello-world-)
- [Tutorials](#tutorials)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Community](#community)
- [Open Governance](#open-governance)
- [Join Us](#join-us)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Get Started

### From PyPi

On Linux/MacOS with Python >= 3.7:

```bash
pip install jina
```

To install Jina with extra dependencies, or install on Raspberry Pi [please refer to the documentation](https://docs.jina.ai).

### In a Docker Container

We provide a universal Docker image that supports multiple architectures (including x64, x86, arm-64/v7/v6). Simply run:

```bash
docker run jinaai/jina --help
```

## Jina "Hello, World!" 👋🌍

As a starter, you can try out our "Hello, World" - a simple demo of image neural search for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No extra dependencies needed, just run:

```bash
jina hello-world
```

...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click here to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>

The Docker image downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set. Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results. The whole process takes about 1 minute, and eventually opens a webpage and shows results like this:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

The implementation behind it is simple:

<table>
<tr>
<td> Python API </td>
<td> or use <a href="https://github.com/jina-ai/jina/blob/master/jina/resources/helloworld.flow.index.yml">YAML spec</a></td>
<td> or use <a href="https://github.com/jina-ai/dashboard">Dashboard</a></td>
</tr>
<tr>
<td>


```python
from jina.flow import Flow

f = (Flow()
        .add(uses='encoder.yml', parallel=2)
        .add(uses='indexer.yml', shards=2,
             separated_workspace=True))

with f:
    f.index(fashion_mnist, batch_size=1024)
```

</td>
<td>

```yaml
!Flow
pods:
  encode:
    uses: encoder.yml
    parallel: 2
  index:
    uses: indexer.yml
    shards: 2
    separated_workspace: true
```

</td>
<td>

![Flow in Dashboard](https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-flow.png?raw=true)

</td>
</tr>
</table>

<details>
<summary><strong>Explore sharding, containerization, concatenating embeddings, and more</strong></summary>

#### Adding Parallelism and Sharding

```python
from jina.flow import Flow

f = (Flow().add(uses='encoder.yml', parallel=2)
           .add(uses='indexer.yml', shards=2, separated_workspace=True))
```

#### [Distributing the Flow](https://docs.jina.ai/chapters/remote/index.html)

```python
from jina.flow import Flow

f = Flow().add(uses='encoder.yml', host='192.168.0.99')
```

#### [Using a Docker Container](https://docs.jina.ai/chapters/hub/index.html)

```python
from jina.flow import Flow

f = (Flow().add(uses='jinahub/cnn-encode:0.1')
           .add(uses='jinahub/faiss-index:0.2', host='192.168.0.99'))
```

#### Concatenating Embeddings

```python
from jina.flow import Flow

f = (Flow().add(name='eb1', uses='BiTImageEncoder')
           .add(name='eb2', uses='KerasImageEncoder', needs='gateway')
           .needs(['eb1', 'eb2'], uses='_concat'))
```

#### [Enabling Network Queries](https://docs.jina.ai/chapters/restapi/index.html)

```python
from jina.flow import Flow

f = Flow(port_expose=45678, rest_api=True)

with f:
    f.block()
```

Intrigued? Play with different options:

```bash
jina hello-world --help
```
</details>

### Create Your First Jina Project

```bash
pip install jina[devel]
jina hub new --type app
```

You can easily create a Jina project from templates with one terminal command. This creates a Python entrypoint, YAML configs and a Dockerfile. You can start from there.


## Tutorials

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

<!-- <tr>
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

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

The best way to learn Jina in depth is to read our documentation. Documentation is built on every push, merge, and release of the master branch.

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

Are you a "Doc"-star? Join us! We welcome all kinds of improvements on the documentation.

[Documentation for older versions is archived here](https://github.com/jina-ai/docs/releases).

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to your active involvement.

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

### Contributors ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-66-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars1.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars3.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars3.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars1.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars3.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars1.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars2.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars1.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars2.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars1.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars1.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://www.imxiqi.com/"><img src="https://avatars2.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://stackoverflow.com/story/umbertogriffo"><img src="https://avatars2.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/lusloher"><img src="https://avatars2.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars0.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars0.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/pswu11"><img src="https://avatars2.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="50px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Community

- [Slack workspace](https://jina-ai.slack.com/messages/general/) - join #general on our Slack to meet the team and ask questions
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

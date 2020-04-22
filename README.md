<p align="center">
  <img src=".github/1500х667.gif?raw=true" alt="Jina banner">
</p>

<p align="center">
 
[![Jina](.github/badges/jina-badge.svg)](https://jina.ai)
[![Jina](.github/badges/jina-hello-world-badge.svg)](#jina-hello-world-)
[![Jina](.github/badges/license-badge.svg)](#jina-hello-world-)
[![Jina Docs](.github/badges/docs-badge.svg)](https://docs.jina.ai)
[![We are hiring](.github/badges/jina-corp-badge-hiring.svg)](https://jina.ai/jobs)
<a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src=".github/badges/twitter-badge.svg"
       alt="tweet button" title="👍Check out Jina: the New Open-Source Solution for Neural Information Retrieval 🔍@JinaAI_"></img>
</a>
[![Python 3.7 3.8](.github/badges/python-badge.svg)](#)
[![Docker](.github/badges/docker-badge.svg)](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)

</p>

<p align="center">
  <a href="https://jina.ai">English</a> •
  <a href="">日本語</a> •
  <a href="">français</a> •
  <a href="">Русский язык</a> •
  <a href="">中文</a>
</p>


<p align="center">
  <a href="https://jina.ai">Website</a> •
  <a href="https://docs.jina.ai">Docs</a> •
  <a href="https://docs.jina.ai">Examples</a> •
  <a href="mailto:newsletter+subscribe@jina.ai">Newsletter</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://board.jina.ai">Dashboard (beta)</a> •
  <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton">Twitter</a> •
  <a href="https://jina.ai/jobs">We are Hiring</a> •
  <a href="https://jina.ai/events">Events</a> •
  <a href="https://blog.jina.ai">Blog</a>
</p>

Want to build a search system backed by deep learning? Then you come to the right place!

**Jina** is *the* cloud-native neural search framework powered by the state-of-the-art AI and deep learning. It is actively maintained by a full-time, [venture-backed team](https://jina.ai).

**🌌 The Universal Search Solution** - Jina enables large-scale index and query of any kind on multiple platforms and architectures. Whether you are searching for images, video clips, audio snippets, long legal documents, short tweets, Jina can handle them all.

**🚀 High Preformat & State-of-the-Art** - Jina aims at AI-in-production. You can easily scale out your VideoBERT, Xception, your word tokenizer, image segmenter and database to handle billion-level data. Features such as replicas and shards come off-the-shelf.

**🐣 System Engineering Made Easy** - Jina offers an one-stop solution that frees you from handcrafting and gluing packages, libraries and database. With the most intuitive API and [dashboard UI](https://github.com/jina-ai/dashboard), building a cloud-native search system is just a minute thing.

**🧩 Powerful Extensions, Simple Integration** - New AI model for Jina? Simply write a Python script or build a Docker image. Plugging in new algorithms has never been that easy, as it should be. Check out [Jina Hub (beta)](https://github.com/jina-ai/jina-hub) and find more extensions on different use-cases contributed by the community.

Jina is an open-source project. [We are hiring](https://jina.ai/jobs) AI engineers, full-stack developers, evangelists, PMs to build *the* next neural search eco-system in open-source. 

## Contents

<img align="right" width="350px" src="./.github/install.png" />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Install](#install)
- [Jina "Hello, World!" 👋🌍](#jina-hello-world-)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Community](#community)
- [Roadmap](#roadmap)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Install

You can install or run Jina via PyPi or Docker container.

#### Install from PyPi
 
On Linux/MacOS with Python >= 3.7 installed, simply run this command in your terminal:

```bash
pip install jina
```

To install Jina with extra dependencies, or install it on Raspberry Pi please refer to the documentations.

#### ...or Run with Docker Container 

We provide a universal Jina image (only 80MB!) that supports multiple architectures (including x64, x86, arm-64/v7/v6), simply do: 

```bash
docker run jinaai/jina
```

## Jina "Hello, World!" 👋🌍

As a starter, we invite you to try Jina's "Hello, World" - a simple demo of image neural search for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No extra dependencies needed, simply do:

```bash
jina hello-world
```

...or even easier for Docker users, *no any install required*, simply:

```bash
docker run -v "$(PWD)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html
```

<details>
<summary>Click here to see the console output</summary>

<p align="center">
  <img src="docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>  

It downloads Fashion-MNIST training and test data and tells Jina to *index* 60,000 images from the training set. Then, it randomly samples images from the test set as *queries*, asks Jina to retrieve relevant results. After about 1 minute, it will open a webpage and show results like this:

<p align="center">
  <img src="docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

And the implementation behind? As simple as it should be:

<table>
<tr>
<td> Python API </td>
<td> index.yml</td>
<td> <a href="https://github.com/jina-ai/dashboard">Flow in Dashboard</a></td>
</tr>
<tr>
<td> 

  
```python
from jina.flow import Flow

f = Flow.load_config('index.yml')

with f.build() as fl:
    fl.index(raw_bytes=input_fn)
```

</td>
<td>
  <sub>

```yaml
!Flow
pods:
  chunk_seg:
    yaml_path: helloworld.crafter.yml
    replicas: $REPLICAS
    read_only: true
  doc_idx:
    yaml_path: helloworld.indexer.doc.yml
  encode:
    yaml_path: helloworld.encoder.yml
    needs: chunk_seg
    replicas: $REPLICAS
  chunk_idx:
    yaml_path: helloworld.indexer.chunk.yml
    replicas: $SHARDS
    separated_workspace: true
  join_all:
    yaml_path: _merge
    needs: [doc_idx, chunk_idx]
    read_only: true
```
</sub>

</td>
<td>

![Flow in Dashboard](docs/chapters/helloworld/hello-world-flow.png)

</td>
</tr>
</table>



All big words you can name: computer vision, neural IR, microservice, message queue, elastic, replicas & shards happened in just one minute!

Intrigued? Play with different options via:

```bash
jina hello-world --help
```

Make sure to continue with our [Jina 101 Guide](https://github.com/jina-ai/jina#jina-101-first-thing-to-learn-about-jina) - understanding all key concepts of Jina in 3 minutes!  


## Getting Started

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="docs/chapters/101/img/ILLUS12.png" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3>Jina 101: First Thing to Learn About Jina</h3>
&nbsp;&nbsp;<a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">English</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.jp.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.fr.md">français</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.cn.md">中文</a>
    </td>

  </tr>
</table>

<table>
<tr><th width="90%">Tutorials</th><th width="10%">Level</th></tr><tr>

<tr>
<td>
<a href="https://jina-ai.github.io/docs/chapters/flow/README.html"><h4>Using Flow API to Compose Your Jina Workflow</h4></a>
Learn how to orchestrate the Pods to work together: sequentially and in parallel; locally and remotely.  
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4>Build Bert-based NLP Semantic Search System in 3 minutes</h4>
Learn how to blah blah blah with blah blah blah
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<a href="https://jina-ai.github.io/docs/chapters/remote/main.html"><h4>Use Jina Distributively</h4></a>
Learn to run Jina in remote and on multiple instances
</td>
<td><h3>🕊</h3></td>
</tr>


<tr>
<td>
<h4>Implement Your First Executor</h4>
Learn how to extend Jina with your own ideas
</td>
<td><h3>🕊</h3></td>
</tr>


<tr>
<td>
<a href="https://github.com/jina-ai/jina-hub#build-your-pod-into-a-docker-image"><h4>Run Jina Pod via Docker Container</h4></a>
Learn how Jina solves complex dependencies easily with Docker container
</td>
<td><h3>🚀</h3></td>
</tr>

<tr>
<td>
<a href="https://github.com/jina-ai/jina-hub#publish-your-pod-image-to-jina-hub"><h4>Share Your Extension with the World</h4></a>
Learn to use Jina Hub and share your extension with engineers from the globe 
</td>
<td><h3>🚀</h3></td>
</tr>

</table>
  

## Documentation 

<a href="https://jina-ai.github.io/docs/">
<img align="right" width="350px" src="./.github/jina-docs.png" />
</a>

The best way to learn Jina in depth is to read our documentation. Documentation is built on every push, merge, and release event of the master branch. You can find more details about the following topics in our documentation.

- [Jina command line interface arguments explained](https://jina-ai.github.io/docs/chapters/cli/main.html)
- [Jina Python API interface](https://jina-ai.github.io/docs/api/jina.html)
- [Jina YAML syntax for executor, driver and flow](https://jina-ai.github.io/docs/chapters/yaml/yaml.html)
- [Jina Protobuf schema](https://jina-ai.github.io/docs/chapters/proto/main.html)
- [Environment variables used in Jina](https://jina-ai.github.io/docs/chapters/envs.html)
- ... [and more](https://jina-ai.github.io/docs/index.html)

Are you are Doc-star? Then join us! We welcome all kinds of improvements on the documentation. 

Documentation of the older version [is archived in here](https://github.com/jina-ai/docs/releases).

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. Without your active involvement, Jina can't be successful.

The following resources help you to make a good first contribution:

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

## Community

- [Slack chanel](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - a communication platform for developers to discuss Jina
- [Community newsletter](mailto:newsletter+subscribe@jina.ai) - subscribe to the latest update, release and event news of Jina
- [LinkedIn](https://www.linkedin.com/showcase/31268045/) - get to know Jina AI as a company
- ![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social) - follow us and interact with us using hashtag `#JinaSearch`  
- [Join Us](mailto:hr@jina.ai) - want to work full-time with us on Jina? We are hiring!
- [Company](https://jina.ai) - know more about our company, we are fully committed to open-source!

## Roadmap

The [GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.

We are looking for partnerships to build a Open Governance model (e.g. Technical Steering Committee) around Jina, which enables a healthy open source ecosystem and developer friendly culture. If you are interested in participating, feel free to contact us at [hello@jina.ai](mailto:hello@jina.ai)


## License

Copyright (c) 2020 Jina AI Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

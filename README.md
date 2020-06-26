<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/1500х667.gif?raw=true" alt="Jina banner" width="100%">
</p>

<p align="center">

[![Jina](https://github.com/jina-ai/jina/blob/master/.github/badges/jina-badge.svg?raw=true  "We fully commit to open-source")](https://jina.ai)
[![Jina](https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true  "Jina is licensed under Apache-2.0")](#license)
[![Python 3.7 3.8](https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true  "Jina supports Python 3.7 and above")](https://pypi.org/project/jina/)
</p>

<p align="center">
  <a href="https://jina.ai">Website</a> •
  <a href="https://docs.jina.ai">Docs</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub</a> •
  <a href="https://dashboard.jina.ai">Dashboard</a> •
  <a href="https://jobs.jina.ai">We are Hiring</a>
</p>

**Jina** is cloud-native neural search, powered by the state-of-the-art AI and deep learning. It has **long-term supported** from a full-time, [venture-backed team](https://jina.ai).

## Features

* **Universal Search** - Large-scale indexing and querying of any kind on multiple platforms and architectures. 
* **High Performance** - Scale out your VideoBERT, Xception, word tokenizer, image segmenter, and database to handle billions of data points. Features like async, replicas, and sharding come out-of-the-box.
* **Easy System Engineering** - One-stop solution that frees you from handcrafting and gluing packages, libraries and databases. 
* **Powerful Extensions** - Extensions are just Python scripts or Docker images. [Check out Jina Hub](https://github.com/jina-ai/jina-hub) to find out more.

[![We are hiring](https://github.com/jina-ai/jina/blob/master/.github/badges/jina-corp-badge-hiring.svg?raw=true  "We are hiring full-time position at Jina")](https://jobs.jina.ai)
Jina is an open-source project. [We are hiring](https://jobs.jina.ai) AI engineers, full-stack developers, evangelists, and PMs to build the next neural search eco-system in open-source.

## Contents

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

## Install [![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/) [![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina is multi-arch ready, can run on different architectures")](https://hub.docker.com/r/jinaai/jina/tags) [![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&label=Docker%20Image&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/jinaai/jina/tags)

With pip:

```bash
pip install jina
```

To install Jina with extra dependencies, or install on Raspberry Pi [please refer to the documentation](https://docs.jina.ai).

With Docker:

```bash
docker run jinaai/jina --help
```

## Try it Out

If you installed Jina with `pip`:

```bash
jina hello-world
```

Or if you used Docker:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click here to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>  

The Docker image downloads Fashion-MNIST training and test data and tells Jina to index 60,000 images from the training set. Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results. The whole process takes about 1 minute, and it'll eventually open a webpage and show results like this:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

As for the implementation behind it? It's as simple as can be:

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

with f:
    f.index(input_fn)
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

![Flow in Dashboard](https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-flow.png?raw=true)

</td>
</tr>
</table>

All the big words you can name: computer vision, neural IR, microservice, message queue, elastic, replicas & shards. They all happened in just one minute!

Intrigued? Play with different options:

```bash
jina hello-world --help
```

[Be sure to continue with our Jina 101 Guide](https://github.com/jina-ai/jina#jina-101-first-thing-to-learn-about-jina) - to understand all key concepts of Jina in 3 minutes!  

## Build your own Project

With [Cookiecutter](https://github.com/cookiecutter/cookiecutter) you can easily create a Jina project from templates with one terminal command. This creates a Python entrypoint, YAML configs and a Dockerfile. You can start from there.

```bash
pip install cookiecutter && cookiecutter gh:jina-ai/cookiecutter-jina
```

## Documentation

The best way to learn Jina in depth is to read our documentation. Documentation is built on every push, merge, and release of the master branch. 

- [Jina 101](https://github.com/jina-ai/jina/tree/master/docs/chapters/101)
- [Get started]()
- [Tutorials]()
- [Command line interface arguments explained](https://docs.jina.ai/chapters/cli/index.html)
- [Python API interface](https://docs.jina.ai/api/jina.html)
- [YAML syntax for Executor, Driver and Flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Protobuf schema](https://docs.jina.ai/chapters/proto/index.html)
- [Environment variables](https://docs.jina.ai/chapters/envs.html)
- ... [and more](https://docs.jina.ai/index.html)

Are you a "Doc"-star? Affirmative? Join us! We welcome all kinds of improvements on the documentation.

## Build Status

[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)  [![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)  [![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)  [![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)  [![API Schema](https://github.com/jina-ai/jina/workflows/API%20Schema/badge.svg)](https://api.jina.ai/)                                                               

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. Without your active involvement, Jina won't be successful.

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

## Community

- [Slack](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - a communication platform for developers to discuss Jina
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - get to know Jina AI as a company and find job opportunities
- [Twitter](https://twitter.com/JinaAI_) - follow us and interact using `#JinaSearch` hashtag
- [Company](https://jina.ai) - know more about our company and how we are fully committed to open-source!

## Roadmap

[GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.

We are looking for partnerships to build a Open Governance model (e.g. Technical Steering Committee) around Jina, to enable a healthy open-source ecosystem and developer-friendly culture. If you are interested in participating, contact us at [hello@jina.ai](mailto:hello@jina.ai).

## License

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [See LICENSE for the full license text.](LICENSE)

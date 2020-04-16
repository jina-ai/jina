![Jina Banner](.github/banner.gif)
<p align="center">
  <img src=".github/banner.gif?raw=true" alt="Jina banner">
</p>


[![Jina](./.github/jina-badge.svg)](https://jina.ai)
<a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src=".github/twitter-badge.svg"
       alt="tweet button" title="👍Check out Jina: the New Open-Source Solution for Neural Information Retrieval 🔍@JinaAI_"></img>
</a>
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)
[![Docker](.github/docker-badge.svg)](https://hub.docker.com/r/jinaai/jina/tags)

<p align="center">
  <a href="https://jina.ai">English</a> •
  <a href="">Русский язык</a> •
  <a href="">français</a> •
  <a href="">日本語</a> •
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


**Jina** is *the* cloud-native neural search solution powered by the state-of-the-art AI and deep learning technology.

**🌌 The Universal Search Solution** - Jina enables large-scale index and query of any kind on multiple platforms and architectures. Whether you are searching for images, video clips, audio snippets, long legal documents, short tweets, Jina can handle them all.

**🐣 System Engineering made Easy** - Jina offers an one-stop solution that frees you from handcrafting and gluing packages, libraries and database. With the most intuitive API and dashboard UI, building a cloud-native search system is just a minute thing.

**🧩 Powerful Extensions, Simple Integration** - New AI model into Jina? Simply write a Python script or build a Docker image. Plugging in new algorithms has never been that easy, as it should be. Checkout Jina Hub (beta) and find more extensions on different use-cases made by the community.

Jina is an open-source project, actively maintained by a full-time, [venture-backed team](https://jina.ai). We are hiring AI engineers, full-stack developers, evangelists to make Jina *the* next neural search eco-system. 

## Contents

<img align="right" width="300px" src="./.github/install.png" />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Install](#install)
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

To install Jina with extra dependencies, or install it on Raspberry Pi and other Linux system, please refer to the documentations.

#### ...or Run with Docker Container 

We provide a universal Jina image (only 80MB!) that can be run on multiple architectures (e.g. x64, x86, arm-64/v7/v6), simply do: 

```bash
docker run jinaai/jina
```

## Getting Started

||||
|---|---|---|
| Jina 101 | Jina important concepts explained | 🐣 |
| Jina 101 | Jina important concepts explained | 🐣 |
| Run Jina in Distributive Way | Learn how to run Jina remotely | 🕊️ |
| Run Jina with Container | Learn how Jina solve dependencies easily with container | 🕊️ |
| Run Jina on Raspberry Pi | Get your Raspberry Pi out of the dust box, time to work  | 🕊️ | 
| Implement Your First Executor | Learn how to extend Jina with your own ideas | 🚀 |
| Share Your Extension with the World | Share your extensions with the world | 🚀 | 
  
## Documentation 

The generated HTML files are hosted in [`jina-ai/jina-docs`](https://github.com/jina-ai/jina-docs).

Documentation is built on every push, merge, and release event of the master branch. 
 
To build the documentation locally, you need to have Docker installed. Clone this repository and run the following command: 

```bash
bash ./make-doc.sh serve 8080
```

The documentation is then available via browser at `http://0.0.0.0:8080/`.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. Without your active involvement, Jina can't be successful.

Please first read [the contributing guidelines](CONTRIBUTING.md) and [our development stages](RELEASE.md) before the submission. 

## Community

- [Slack chanel](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - a communication platform for developers to discuss Jina
- [Community newsletter](mailto:newsletter+subscribe@jina.ai) - subscribe to the latest update, release and event news of Jina
- [LinkedIn](https://www.linkedin.com/showcase/31268045/) - get to know Jina AI as a company
- ![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social) - follow us and interact with us using hashtag `#JinaSearch`  
- [Join Us](mailto:hr@jina.ai) - want to work full-time with us on Jina?
- [Company](https://jina.ai) - know more about our company, we are fully committed to open-source!

## Roadmap

The [GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.


## License

If you have downloaded a copy of the Jina binary or source code, please note that Jina's binary and source code are both licensed under the [Apache 2.0](LICENSE).

# Jina

[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ARelease%20Cycle)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ARelease%20CD)
[![Docker](.github/docker-badge.svg)](https://hub.docker.com/r/jinaai/jina/tags)

Jina is *the* cloud-native neural search solution powered by the state-of-the-art AI and deep learning technology.

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

#### Upgrade Jina

If you have a previously installed version, you can upgrade it by running:

```bash
pip install -U jina
```

or 

```bash
docker pull jinaai/jina
```

A complete guide of using Jina with Docker can be found in our documentation.

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

Please first read [the contributing guidelines](CONTRIBUTING.md) before the submission. 

## Community

- Slack chanel - a communication platform for developers to discuss Jina
- Mailing list - subscribe to the latest update, release news of Jina
- [LinkedIn](https://www.linkedin.com/showcase/31268045/) - get to know Jina AI as a company
- [Twitter](https://twitter.com/JinaAI_) - interact with us @JinaAI_  
- [Join Us](mailto:hr@jina.ai) - want to work full-time with us on Jina?


## Roadmap

The [GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.


## License

If you have downloaded a copy of the Jina binary or source code, please note that Jina's binary and source code are both licensed under the [Apache 2.0](LICENSE).

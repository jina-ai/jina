# Jina

[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Docker](.github/docker-badge.svg)](https://hub.docker.com/r/jinaai/jina/tags)

Jina is *the* cloud-native neural search solution powered by the state-of-the-art AI and deep learning technology.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Install](#install)
  - [...or Run with Docker Container](#or-run-with-docker-container)
- [Testing](#testing)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Install

You can install or run Jina via PyPi or Docker container.

#### Install from PyPi
 
On Linux/Mac with Python >= 3.7 installed, simply do:

```bash
pip install jina
```

To install Jina with extra dependencies, or install it on Raspberry Pi and other Linux system, please refer to the documentations.

#### ...or Run with Docker Container 

We provide a universal container image as small as 80MB that can be run on multiple architectures (e.g. x64, x86, arm-64/v7/v6), simply do: 

```bash
docker run jinaai/jina:master-debian
```

A complete guide of using Jina with Docker can be found in our documentation.

## Testing

To verify the installation:

```bash
jina check

# or 

docker run jinaai/jina:master-debian check
```

It prints a list of components the current Jina supported and exits.

If you cloned this repository to local, then you can perform unittest via:

```bash
cd tests && python -m unittest *.py -v
```
  
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

## Roadmap

The [GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.


## License

If you have downloaded a copy of the Jina binary or source code, please note that Jina's binary and source code are both licensed under the [Apache 2.0](LICENSE).

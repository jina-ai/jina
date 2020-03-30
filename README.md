# Jina

[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Docker](.github/docker-badge.svg)](https://hub.docker.com/r/jinaai/jina/tags)

Jina is *the* cloud-native neural search solution powered by the state-of-the-art AI and deep learning technology.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Getting Started](#getting-started)
  - [Running Jina Image](#running-jina-image)
  - [Running Jina Natively](#running-jina-natively)
- [Testing](#testing)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Getting Started

The simplest way to use Jina is via Docker. We provide a universal container image as small as 100MB that can be run on multiple architectures (e.g. x64, x86, arm-64/v7/v6). Of course, you need to have [Docker installed](https://docs.docker.com/install/) first. 

### Running Jina Image

```bash
docker run jinaai/jina:master-debian
```

This command downloads the latest Jina image from [Docker Hub](https://hub.docker.com/r/jinaai/jina/tags) based on your local architecture and then runs it in a container. When the container runs, it prints an help message and exits.

<details>
 <summary>Other Jina docker image mirrors: (click to expand...)</summary>

> 🚨 We have stopped updating these two registries. They are just listed here for reference and they will be deleted anytime soon.

#### Github Package (Do not support multiarch)

```bash
docker login -u USERNAME -p TOKEN docker.pkg.github.com
docker run docker.pkg.github.com/jina-ai/jina/jina:[tag]
```

#### Tencent Cloud (Too slow to upload)

```bash
docker login -u USERNAME -p TOKEN ccr.ccs.tencentyun.com
docker run ccr.ccs.tencentyun.com/jina/jina:[tag]
```
</details>

### Running Jina Natively

If you prefer the classic way to run Jina natively on the host, please make sure you have Python >= 3.7 installed on the host. 

#### Install from PyPi
 
```bash
pip install jina
```

#### ...or Install from the Master Branch

```bash
pip install git+https://github.com/jina-ai/jina.git
```

#### ...or (Dev/Editable mode) Install from Your Local Folk/Clone 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e .
``` 

> Note, if you later switch to the other ways of Jina installation, remember to first uninstall the editable version from the system:
  ```bash
  pip uninstall $(basename $(find . -name '*.egg-info') .egg-info)
  ```

## Testing

To verify the installation:

```bash
docker run jinaai/jina:master-debian check

# or if you installed Jina locally
jina check
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

## Roadmap

The [GitHub milestones](https://github.com/jina-ai/jina/milestones) lay out the path to the future improvements.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. Without your active involvement, Jina can't be successful.

Please first read [the contributing guidelines](CONTRIBUTING.md) before the submission. 

## License

If you have downloaded a copy of the Jina binary or source code, please note that Jina's binary and source code are both licensed under the [Apache 2.0](LICENSE).

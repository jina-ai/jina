# Jina

![Unit Test Status Badge](https://github.com/jina-ai/jina/workflows/Unit%20Test/badge.svg)
![Docker Build](https://github.com/jina-ai/jina/workflows/Docker%20BuildX/badge.svg?branch=master)
![Docs Build](https://github.com/jina-ai/jina/workflows/Docs%20Build/badge.svg?branch=master)


Jina is *the* cloud-native neural search solution powered by the state-of-the-art AI and deep learning technology.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Getting Started](#getting-started)
  - [Run the Container Image](#run-the-container-image)
  - [Run without Container](#run-without-container)
- [Test Your Installation](#test-your-installation)
- [Documentation](#documentation)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Getting Started

The simplest way to use Jina is via Docker. We provide a universal container image as small as 100MB that can be run on multiple architectures (e.g. x64, x86, arm-64/v7/v6). Of course, you need to have [Docker installed](https://docs.docker.com/install/) first. 

### Running an Jina Image

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

### Running Jina Natively on the Host

If you prefer the classic way to run Jina natively on the host, please make sure you have Python >= 3.7 installed on the host. 

#### Install from PyPi

To install the latest stable release:
 
```bash
pip install jina
```

#### Or, Install from This Git Repository

To install the latest master:

```bash
pip install git+https://github.com/jina-ai/jina.git
```

#### Or, (Dev mode) Install from Your Local Folk/Clone 

For developers who want to edit the project’s code and test the changes on-the-fly, 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e .
``` 

Note, if you later want to switch to the other ways of Jina installation, remember to first uninstall your editable version from the system:

```bash
pip uninstall $(basename $(find . -name '*.egg-info') .egg-info)
```

## Testing

If you installed Jina locally, you can verify the installation via:

```bash
jina check
```

It prints a list of components the current Jina supported and exits.

If you cloned this repository to local, then you can perform unittest via:

```bash
cd tests && python -m unittest *.py -v
```
  
## Documentation 

The generated HTML files are hosted in a separate repository [`jina-ai/jina-docs`](https://github.com/jina-ai/jina-docs).

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

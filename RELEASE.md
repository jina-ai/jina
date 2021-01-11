# Release Cycle

[![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina is multi-arch ready, can run on different architectures")](https://hub.docker.com/r/jinaai/jina/tags)
[![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&label=Docker%20Image&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)
[![API Schema](https://github.com/jina-ai/jina/workflows/API%20Schema/badge.svg)](https://api.jina.ai/)

## PyPi Versioning 

We follow the [semantic versioning](https://semver.org/), numbered with `x.y.z`. By default, `pip install jina` always install the latest release. To install a particular version from PyPi, please use:

```bash
pip install jina==x.y.z
```

## Docker Image Versioning

The docker image name starts with `jinaai/jina` followed by a tag composed as four parts:

```text
jinaai/jina:{version}{dependency}{python_version}{entrypoint}
```

- `{version}`: The version of Jina. Possible values:
    - `latest`: the last release;
    - `master`: the master branch of `jina-ai/jina` repository;
    - `x.y.z`: the release of a particular version;
    - `x.y`: the alias to the last `x.y.z` patch release;
- `{dependency}`: the extra dependency installed along with Jina. Possible values:
    - ` `: Jina is installed inside the image via `pip install jina`;
    - `-devel`: Jina is installed inside the image via `pip install jina[devel]`;
- `{python-version}`: The Python version of the image. Possible values: ` `, `-py37`, `-py38` for Python 3.7 and Python 3.8 respectively, where ` ` means Python 3.7.
- `{entrypoint}`: The entrypoint of the image. Possible values: ` `, `-daemon`, where ` ` means default Jina entrypoint.

Examples:

- `0.9.6`: the `0.9.6` release with Python 3.7 and the entrypoint of default Jina.
- `latest-py38-daemon`: the latest release with Python 3.8 base and the entrypoint of Jina daemon.

### Do I need `-devel`?

Use `-devel` image, if you want to use:
- REST interface
- Jina daemon (use `-daemon`)
- Dashboard
- Log-streaming 

### Image Alias & Update

On every master merge, the following images got updated:

- `jinaai/jina:master{dependency}{python_version}{entrypoint}`

, where:
  - dependency: `["", "-devel"]`
  - python_version: `["-py37", "-py38"]`
  - entrypoint: `["", "-daemon"]`

On every `x.y.z` release, the following images got update:

- `latest{dependency}{python_version}{entrypoint}`
- `x.y.z{dependency}{python_version}{entrypoint}`
- `x.y{dependency}{python_version}{entrypoint},`

, `latest` & `x.y.z` & `x.y` are aliases, and where
  - dependency: `["", "-devel"]`
  - python_version: `["-py37", "-py38"]`
  - entrypoint: `["", "-daemon"]`
  

### Image Size of Different Versions

![](https://img.shields.io/docker/image-size/jinaai/jina/latest?label=jinaai%2Fjina%3Alatest&logo=docker)
![](https://img.shields.io/docker/image-size/jinaai/jina/latest-devel?label=jinaai%2Fjina%3Alatest-devel&logo=docker)
![](https://img.shields.io/docker/image-size/jinaai/jina/latest-daemon?label=jinaai%2Fjina%3Alatest-daemon&logo=docker)
![](https://img.shields.io/docker/image-size/jinaai/jina/master?label=jinaai%2Fjina%3Amaster&logo=docker)

The last update image is ![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?label=last%20update&logo=docker&sort=date) 

## Master Update

Every successful merge into the master triggers a development release. It will: 

- update the Docker image with tag `devel`;
- update [jina-ai/docs](https://github.com/jina-ai/docs) tag `devel`

Note, commits started with `chore` are exceptions and will not trigger the events above. Right now these commits are:

- `chore(docs): update TOC`
- `chore(version): bumping master version`

## Sunday Auto Release

On every Sunday 23pm, a patch release is scheduled:

- tag the master as `vx.y.z` and push to the repo;
- create a new tag `vx.y.z` in [jina-ai/docs](https://github.com/jina-ai/docs);
- publish `x.y.z` docker image, with tag `latest`, `x.y.z`;
- upload `x.y.z` package on PyPI;
- bump the master to `x.y.(z+1)` and commit a `chore(version)` push.

The current master version should always be one version ahead of `git tag -l | sort -V | tail -n1`.

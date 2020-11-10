# Release Cycle

[![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina is multi-arch ready, can run on different architectures")](https://hub.docker.com/r/jinaai/jina/tags)
[![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&label=Docker%20Image&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)
[![API Schema](https://github.com/jina-ai/jina/workflows/API%20Schema/badge.svg)](https://api.jina.ai/)


We follow the [semantic versioning](https://semver.org/), numbered with `x.y.z`.

## Version Explained

| Tag | Description |
| --- | --- |
| `latest` | the last Friday release, contains the bare minimum of to run Jina framework. |
| `x.y.z` | (previous) Friday release. |
| `devel` | the development version corresponds to the latest master, it extends `latest` by adding required packages for [Dashboard](https://github.com/jina-ai/dashboard). |
| `x.y.z-devel` | (previous) `devel` version of `x.y.z` |

### Which Version to Use?

- Use `latest`, if you want to use barebone Jina framework and extend it with your own modules/plugins.
- Use `devel`, if you want to use [Dashboard](https://github.com/jina-ai/dashboard) to get more insights about the logs and flows.

### Docker Image Size of Different Versions

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/jinaai/jina/latest?label=jinaai%2Fjina%3Alatest&logo=docker)

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/jinaai/jina/devel?label=jinaai%2Fjina%3Adevel&logo=docker)

The last update image is ![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?label=last%20update&logo=docker&sort=date)  

## Master Update

Every successful merge into the master triggers a development release. It will: 

- update the Docker image with tag `devel`;
- update [jina-ai/docs](https://github.com/jina-ai/docs) tag `devel`

Note, commits started with `chore` are exceptions and will not trigger the events above. Right now these commits are:

- `chore(docs): update TOC`
- `chore(version): bumping master version`

## Friday Release

On Friday release, it will:

- tag the master as `vx.y.z` and push to the repo;
- create a new tag `vx.y.z` in [jina-ai/docs](https://github.com/jina-ai/docs);
- publish `x.y.z` docker image, with tag `latest`, `x.y.z`;
- upload `x.y.z` package on PyPI;
- bump the master to `x.y.(z+1)` and commit a `chore(version)` push.

The current master version should always be one version ahead of `git tag -l | sort -V | tail -n1`.

## Nightly Release

Every midnight at 0:00, the docker image tagged with `x.y.z-devel` will be rebuilt on all platforms, include: linux/amd64, linux/arm64, linux/ppc64le, linux/s390x, linux/386, linux/arm/v7, linux/arm/v6.
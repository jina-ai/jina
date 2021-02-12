# Release & Version Identifier

Jina is shipped from two package management systems, PyPi and Docker Hub. This article clarifies the release cycle and version identifier behind each system.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [PyPi package versioning](#pypi-package-versioning)
- [Docker image versioning](#docker-image-versioning)
- [Manual Release Entrypoint](#manual-release-entrypoint)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## PyPi package versioning 

We follow the [semantic versioning](https://semver.org/) and [PEP-440](https://www.python.org/dev/peps/pep-0440/). Jina's version is identified by `x.y.z` (i.e. "major.minor.patch").
 
To install the latest final release:
 
```bash
pip install -U jina
```

To install a particular final release:

```bash
pip install jina==x.y.z
```

The term "final release" is relative to "developmental release" as described below.  

### Developmental releases versioning

One every master-merging event, we create early releases directly from source control which do not conflict with later project releases. The version identifier for development release is `x.y.z.devN`, which adds a suffix `.dev`, followed by a non-negative integer value `N`, which is reset on every release.

To install the latest development release:

```bash
pip install --pre jina
```

### Version epochs

The following example shows how Jina is released from 0.9 to 0.9.2 according to the schema we defined above.

|Event `e` | After `e`, `pip install jina` | After `e`, `pip install --pre jina` | After `e`, master `__init__.py` |
|--- | ---  | --- | --- |
| Release | 0.9.0 | 0.9.0 | 0.9.1.dev0 |
| Master merging | 0.9.0 | 0.9.1.dev0 | 0.9.1.dev1 |
| Master merging | 0.9.0 | 0.9.1.dev1 | 0.9.1.dev2 |
| Master merging | 0.9.0 | 0.9.1.dev2 | 0.9.1.dev3 |
| Release | 0.9.1 | 0.9.1 | 0.9.2.dev0 |
| Master merging | 0.9.1 | 0.9.2.dev0 | 0.9.2.dev1 |

## Docker image versioning

Our univeral Docker image is ready-to-use on linux/amd64, linux/armv7+, linux/arm/v6. The Docker image name always starts with `jinaai/jina` followed by a tag composed of three parts:

```text
jinaai/jina:{version}{python_version}{extra}
```

- `{version}`: The version of Jina. Possible values:
    - `latest`: the last release;
    - `master`: the master branch of `jina-ai/jina` repository;
    - `x.y.z`: the release of a particular version;
    - `x.y`: the alias to the last `x.y.z` patch release, i.e. `x.y` = `x.y.max(z)`;
- `{python_version}`: The Python version of the image. Possible values: 
    - ` `, `-py37`: Python 3.7;
    - `-py38` for Python 3.8;
    - `-py39` for Python 3.9;
- `{extra}`: the extra dependency installed along with Jina. Possible values:
    - ` `: Jina is installed inside the image via `pip install jina`;
    - `-devel`: Jina is installed inside the image via `pip install jina[devel]`;
    - `-daemon`: Jina is installed inside the image via `pip install jina[dameon]` along with `fluentd`; **and the entrypoint is set to `jinad`**.

Examples:

- `jinaai/jina:0.9.6`: the `0.9.6` release with Python 3.7 and the entrypoint of `jina`.
- `jinaai/jina:latest-py38-daemon`: the latest release with Python 3.8 base and the entrypoint of Jina daemon.
- `jinaai/jina:latest`: the latest release with Python 3.7 and the entrypoint of `jina`
- `jinaai/jina:master`: the master with Python 3.7 and the entrypoint of `jina`

### Do I need `-devel`?

Use `-devel` image, if you want to:
- have efficiency improvement on AsyncIO and data compression
- enable prettified error printing
- build Jina Hub extension
- expose REST interface beyond gRPC
- enable log-streaming/aggregating via `fluentd`
- enable mime-type sniffing

### Image alias and updates

| Event | Updated images | Aliases |
| --- | --- | --- |
| On Master Merge | `jinaai/jina:master{python_version}{extra}` | |
| On `x.y.z` release | `jinaai/jina:x.y.z{python_version}{extra}` | `jinaai/jina:latest{python_version}{extra}`, `jinaai/jina:x.y{python_version}{extra}` |

Six images are built, i.e. taking the combination of: 
  - `{python_version} = ["-py37", "-py38"]`
  - `{extra} = ["", "-devel", "-daemon"]`


### Image size on different tags

|Image Size|
| ---|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest?label=jinaai%2Fjina%3Alatest&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py38?label=jinaai%2Fjina%3Alatest-py38&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py39?label=jinaai%2Fjina%3Alatest-py39&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-devel?label=jinaai%2Fjina%3Alatest-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-daemon?label=jinaai%2Fjina%3Alatest-daemon&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py38-devel?label=jinaai%2Fjina%3Alatest-py38-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py38-daemon?label=jinaai%2Fjina%3Alatest-py38-daemon&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py39-devel?label=jinaai%2Fjina%3Alatest-py39-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/latest-py39-daemon?label=jinaai%2Fjina%3Alatest-py39-daemon&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master?label=jinaai%2Fjina%3Amaster&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py38?label=jinaai%2Fjina%3Amaster-py38&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py39?label=jinaai%2Fjina%3Amaster-py39&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-devel?label=jinaai%2Fjina%3Amaster-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-daemon?label=jinaai%2Fjina%3Amaster-daemon&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py38-devel?label=jinaai%2Fjina%3Amaster-py38-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py38-daemon?label=jinaai%2Fjina%3Amaster-py38-daemon&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py39-devel?label=jinaai%2Fjina%3Amaster-py39-devel&logo=docker)|
|![](https://img.shields.io/docker/image-size/jinaai/jina/master-py39-daemon?label=jinaai%2Fjina%3Amaster-py39-daemon&logo=docker)|

## Manual Release Entrypoint

Manual release entrypoint is designed for authroized core developers of Jina. 

### Trigger weekly release manually

One can release a hotfix immediately without waiting for the weekly release. Here are the steps:

1. [Go to here](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Manual+Release%22)
2. Click on "Run Workflow" dropdown button on the right and input the release token and the release reason.
3. Click on "Run Workflow" green button.

### Rebuild all Docker images for certain `git tag` manually

1. [Go to here](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Manual+Docker+Build%22)
2. Click on "Run Workflow" dropdown button on the right and input the release token and the release reason.
3. Click on "Run Workflow" green button.

![Rebuild all Docker images](.github/images/manual-docker-build.png)

Note, the manual rebuild on Docker images will *NOT* update `:latest-*` and `:x.y-*` aliases.
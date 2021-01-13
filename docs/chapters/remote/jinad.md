# Jina Daemon

`jinad`, aka `Jina Daemon`, is a persistent process for deploying and managing Jina Flow, Pods, and Peas in a distributed system. 

## Design

`jinad` is designed to maintain bookkeeping for the running Flows, Pods and Peas on the remote machines. `jinad` can also spawn Pods and Peas to other remote machines that have `jinad` running. [`fluentd`](https://github.com/fluent/fluentd) is used to collect logs from different Processes and ensure the logs belonging to the same Flow are stored consistently. 

![jinad design](jinad_design.png)

## Installation

### Using Docker Images (Recommended)

The simplest way to use `jinad` is via Docker. There is no need to worry about fluent installation. You only need to have [Docker installed](https://docs.docker.com/install/) first. 

In the command below, we use the tag `latest-daemon` which uses the latest release version of `jinad`. Of course, you can switch to other versions, and you can find all the available versions at [hub.docker.com](https://hub.docker.com/repository/docker/jinaai/jina/tags?page=1&ordering=last_updated&name=daemon). You can found more information about the versioning at [github.com/jina-ai/jina](https://github.com/jina-ai/jina/blob/master/RELEASE.md).

```bash
docker pull jinaai/jina:latest-daemon
```

### Using PyPi package

On Linux/Mac, simply run:

```bash
pip install "jina[daemon]"
```

## Install from the Master Branch

If you want to keep track of the master branch of our development repository:

```bash
pip install "git+https://github.com/jina-ai/jina.git#egg=jina[daemon]"
```

### Install from Your Local Fork/Clone

If you are a developer and want to test your changes on-the-fly: 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e ".[daemon]"
``` 

For more information about PyPi installation, please refer to the [general PyPi installation instructions of jina](https://docs.jina.ai/chapters/install/via-pip.html) and replace ```

## Usage 
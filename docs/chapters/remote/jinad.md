# Jina Daemon

`jinad`, aka `Jina Daemon`, is a persistent process for deploying and managing Jina Flow, Pods, and Peas in a distributed system. 

## Terminologies

- *Workflow*: a set of connected pods for accomplishing certain task, e.g. indexing, searching, extracting.
- *Flow API*: a pythonic way for users to construct workflows in Jina with clean, readable idioms. 
- *Remote*, *remote instance*, *remote machine*: the place where you want to run the pod, the place offers better computational capability or larger storage. For example, one may want to run an encode pod on the remote GPU instance.  
- *Local*, *local instance*, *local machine*: the place of your entrypoint and the rest parts of your workflow.

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

> Notes: As one part of the jina package, `jinad` follows the same [installation instructions of jina](https://docs.jina.ai/chapters/install/via-pip.html) and you only need to cherry pick `[daemon]`

On Linux/Mac, simply run:

```bash
pip install "jina[daemon]"
```

### Install from the Master Branch

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

## Usage 

### Prerequisites
Run `jinad` on the remote machine. We assume the remote is in the intranet and its IP address is `12.34.56.78`. By default, `jinad` will use the port `8000` for receiving requests. Make sure `8000` port is publicly accessible.

After having `jinad` running on the remote, you can open the browser the visit `http://3.16.166.3:8000/alive` to check whether `jinad` is properly set up. If everythong works well, you will see the following response.

```json
{"status_code":200,"jina_version":"0.9.12"}
```

#### Using Docker Container

We start a Docker container under the `host` mode so that it will connect all the ports to the host machine. `-d` option is to keep the container running in the background

```bash
docker run -d --network host jinaai/jina:latest-daemon
```

#### Using Native Python

```bash
jinad
```

### Creating a Remote Pod from Console
In the simplest case, you may want to create a Pod on the remote. The most naive way is to log into the remote machine and start a pod using `jina` CLI [link to run-remote-pod-console](). To avoid logging into the remote machine every time, we can use `jinad` to do the same thing. Furthermore, `jinad` offers a better session management for the running Pods on the remote.

Here we start a simple Pod with the default configuration `_logforward`. The Pod forwards received messages and print the messages out in the logs. On the local, you can run the following command to start a remote pod.

```bash
jina pod --uses _logforward --host 3.16.166.3 --port-expose 8000
```

```text
▶️  /Users/nanwang/.pyenv/versions/3.7.5/bin/jina pod --uses _logforward --host 3.16.166.3 --port-expose 8000
...
   JinadRuntime@68880[S]:created remote pod with id dcb5046e-554a-11eb-86b2-0ab9db700358
        BasePea@68861[S]:ready and listening
   JinadRuntime@68880[I]:🌏 Fetching streamed logs from remote id: dcb5046e-554a-11eb-86b2-0ab9db700358
   🌏 ZEDRuntime@68880[I]:input tcp://0.0.0.0:55223 (PULL_BIND) output tcp://0.0.0.0:55535 (PUSH_BIND) control over tcp://0.0.0.0:49993 (PAIR_BIND)
      🌏 BasePea@68880[I]:ready and listening
```

The logs starting with 🌏 are fetched from the remote Pod. Now we have already the Pod running remotely and we can check the connectivity.

```bash
jina ping 3.16.166.3 49993
```

```text
▶️  /Users/nanwang/.pyenv/versions/3.7.5/bin/jina ping 3.16.166.3 49993
...
           JINA@69179[I]:ping tcp://3.16.166.3:49993 at 2 round...
           JINA@69179[I]:ping tcp://3.16.166.3:49993 at 2 round takes 1 second (1.23s)
           JINA@69179[S]:avg. latency: 1343 ms
```

### Creating a Remote Pod via Flow API 

### Creating a Remote Flow

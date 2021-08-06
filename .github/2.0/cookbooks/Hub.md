<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Hubble CLI Guidelines](#hubble-cli-guidelines)
  - [Prerequisites](#prerequisites)
  - [1. Create Executor](#1-create-executor)
  - [2. Push and Pull CLI](#2-push-and-pull-cli)
    - [2.1 Distribute your executor](#21-distribute-your-executor)
    - [2.2 Pull distributed executor](#22-pull-distributed-executor)
  - [3. Use in Jina Flow](#3-use-in-jina-flow)
    - [3.1 Using docker images](#31-using-docker-images)
    - [3.2 Using source codes](#32-using-source-codes)
    - [3.3 Override Default Parameters](#33-override-default-parameters)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# JinaHub Guidelines

## Prerequisites

- [Docker](https://docs.docker.com/get-docker) installed.
- `jina[standard] >= 2.0.0` installed.
    - Run `pip install -U "jina[standard]>=2.0.0"` to upgrade jina to correct version.

## 1. Create Executor

To create your Executor, you just need to run this command in your terminal:

```terminal
jina hub new
```

A wizard will ask you some questions about the Executor. For the basic configuration, you will be asked two things: The Executor’s name and where it should be saved. For this tutorial, we will call ours RequestLogger. And you can save it wherever you want to have your project. The wizard will ask if you want to have a more advanced configuration, but it is unnecessary for this tutorial.

## 2. Push Executor to JinaHub

If you want to share your executors to other persons or colleges, you can push your local executor to JinaHub.

### 2.1 Basic

```bash
$ jina hub push [--public/--private] <path_to_executor_folder>
```

It will return an **UUID** as well as a **SECRET**. You would need these two items when using or update the executor later. **Please keep them carefully.**

**Notes**:

- When no `--public` or `--private` visibility options are provided. **By default, it's public.**
- There is only one difference between `--public` and `--private`. You can use public executor once you know the `UUID`, but you must know `SECRET` and `UUID` if you want to use a private executor.

### 2.2 Advanced

```bash
$ jina hub push <path_to_executor_folder> -t TAG1 -t TAG2 -f <path_to_dockerfile>
```

You can specify `-t` or `--tags` parameters to tag one executor. In additional, you can specify `-f` or `--docker-file` parameters to use a specific docker file to build your executor.

## 3. Update Executor in JinaHub

Everything is iterating in Internet world. We also provide a way to update your existing executor in JinaHub. To update one executor, you must have both `UUID` and `SECRET`.

```bash
$ jina hub push [--public/--private] --force <UUID> --secret <SECRET> <path_to_executor_folder>
```

**Notes**:
- With `--public` option, the resulted executor will be **visible to public**.
- With `--private` options, the resulted executor will be **invisible to public**.

## 4. Pull Executor from JinaHub

`Pull` means fetching the executor content to your local machine. For each executor, there are two different format content for user to pull.

### 4.1 Docker Image

```bash
$ jina hub pull jinahub+docker://<UUID>[:<SECRET>]
```

You can find the executor by running this command `docker images`.

### 4.2 Source Code

```bash
$ jina hub pull jinahub://<UUID>[:<SECRET>]
```

It will store executor source code to `~/.jina/hub-packages`.

**Note**:

- For public executor, you can ignore the `SECRET` option.
- For private executor, you must provide the `SECRET` option.

## 5. Use in Jina Flow

It will pull executor automatically if you didn't pull it before.

### 5.1 Using docker images

Use the prebuilt images from `Hubble` in your python codes,

```python
from jina import Flow

# SECRET must be provided for private executor
f = Flow().add(uses='jinahub+docker://<UUID>[:<SECRET>][/<TAG>]')
```

**Attention:**

If you are a Mac user, please use `host.docker.internal` as your url when you want to connect a local port from executor
docker container.

For
example: [`jinahub+docker://PostgreSQLStorage`](https://github.com/jina-ai/executor-indexers/tree/main/jinahub/indexers/storage/PostgreSQLStorage)
will connect PostgreSQL server which was started at local. Then you must use it with:

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+docker://PostgreSQLStorage', 
               uses_with={'hostname': 'host.docker.internal'})
with f:
    resp = f.post(on='/index', inputs=Document(), return_results=True)
    print(f'{resp}')
```

### 5.2 Using source codes

Use the source codes from `Hubble` in your python codes,

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]')
```

### 5.3 Override Default Parameters

It is possible that the default parameters of the published executor may not be ideal for your usecase. You can override
any of these parameters by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>]', 
               uses_with={'param1': 'new_value'},
               uses_metas={'name': 'new_name'})
```

This way, the executor will work with the overriden parameters.

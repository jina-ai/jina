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

# Hubble CLI Guidelines

## Prerequisites

- [Docker](https://docs.docker.com/get-docker) installed.
- `jina[standard] >= 2.0.0` installed.
    - Run `pip install -U "jina[standard]>=2.0.0"` to upgrade jina to correct version.

## 1. Create Executor

The resulted file structure should look like the following:

```text
MyExecutor/
├── Dockerfile	        # Optional
├── manifest.yml	    # Optional 
├── config.yml	        # Optional
├── README.md	        # Optional
├── requirements.txt	# Optional
├── __init__.py
├── setup.py	        # Optional
└── tests/	            # Optional
    ├── test_MyAwesomeExecutor.py
    └── __init__.py

```

Link to the _**detailed guidelines**_ for creating an executor
is [here](https://github.com/jina-ai/executor-template/blob/main/.github/GUIDELINES.md).

## 2. Push and Pull CLI

### 2.1 Distribute your executor

1. Push your local executor (without `--force`)
    ```bash
    $ jina hub push [--public/--private] <your_folder>
    ```
   _**Note**_:
    - When no `--public` or `--private` visibility options are provided. **By default, it's public.**
    - Returns a **UUID8** as well as a **SECRET**. You can use it in `Jina flow`
      via `.add(uses='jinahub://<UUID8/Alias>')` or `.add(uses='jinahub+docker://<UUID8/Alias>')`
    - For public executor, you have read access if you have `UUID8`, you have write access if you have `SECRET`


2. Update your local executor (with `--force`)
    ```bash
    $ jina hub push [--public/--private] --force <UUID8/Alias> --secret <SECRET> <your_folder>
    ```
   _**Note**_:
    - Without any visibility option, it will only update the content of exexited executor.
    - With `--public` option, the resulted executor will be **visible to public**.
    - With `--private` options, the resulted executor will be **invisible to public**.

### 2.2 Pull distributed executor

- Pull the executor's **docker image**
    ```bash
    $ jina hub pull jinahub+docker://<UUID8/Alias>[:<SECRET>]
    ```
- Pull the executor's **source-code package** into `~/.jina/hub-executors` defaultly
    ```bash
    $ jina hub pull jinahub://<UUID8/Alias>[:<SECRET>]
    ```

  _**Note**_:
    - For public executor, you can ignore the `SECRET` option.
    - For private executor, you must provide the `SECRET` option.

## 3. Use in Jina Flow

### 3.1 Using docker images

Use the prebuilt images from `Hubble` in your python codes,

```python
from jina import Flow

# SECRET must be provided for private executor
f = Flow().add(uses='jinahub+docker://<UUID8/Alias>[:<SECRET>]')
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

### 3.2 Using source codes

Use the source codes from `Hubble` in your python codes,

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID8/Alias>[:<SECRET>]')
```

### 3.3 Override Default Parameters

It is possible that the default parameters of the published executor may not be ideal for your usecase. You can override
any of these parameters by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID8/Alias>[:<SECRET>]', 
               uses_with={'param1': 'new_value'},
               uses_metas={'name': 'new_name'})
```

This way, the executor will work with the overriden parameters.

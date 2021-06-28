# Hubble CLI Guildlines

**WARNING**: The developing branch is `fix-hubble-test`, which is not production ready.  You should expect API changes, failures, etc.

If you have any problems to work with `Hubble` cli, please raise this up in the `proj-hubble` channel

## Prerequisites

- Install [Docker](https://docs.docker.com/get-docker).
- working on `fix-hubble-test` branch (_before stable Jina 2.0_)
    ```bash
    $ git clone --branch fix-hubble-test https://github.com/jina-ai/jina.git
    $ cd jina && pip install -e ".[devel]"
    ```

## 1. Create Executor

The resulted file structure should look like the following:

```text
MyExecutor/
├── Dockerfile	        # Optional
├── manifest.yml	# Optional 
├── config.yml	        # Optional
├── README.md	        # Optional
├── requirements.txt	# Optional
├── __init__.py
├── setup.py	        # Optional
└── tests/	           # Optional
    ├── test_MyAwesomeExecutor.py
    └── __init__.py

```

Link to the _**detailed guidlines**_ for creating an executor is [here](https://github.com/jina-ai/executor-template/blob/main/.github/GUIDELINES.md).

## 2. Push and Pull CLI

### 2.1 Distribute your executor

1. Push your local executor (without `--force`)
    ```bash
    $ jina hub push [--public/--private] <your_folder>
    ```
    _**Note**_: 
    - When no `--public` or `--private` visibility options are provided. **By default, it's public.**
    - Returns a **UUID8** as well as a **SECRET**. You can use it in `Jina flow` via `.add(uses='jinahub://<UUID8/Alias>')` or `.add(uses='jinahub+docker://<UUID8/Alias>')`
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

### 3.2 using docker images

Use the prebuilt images from `Hubble` in your python codes, 

```python
from jina import Flow

# SECRET must be provided for private executor
f = Flow().add(uses='jinahub+docker://<UUID8/Alias>[:<SECRET>]')
```

### 3.2 using source codes

Use the source codes from `Hubble` in your python codes,

```python
from jina import Flow
	
f = Flow().add(uses='jinahub://<UUID8/Alias>[:<SECRET>]')
```



# Welcome to Jina!

```{include} ../README.md
:start-after: <!-- start jina-description -->
:end-before: <!-- end jina-description -->
```

## Install

1. Make sure that you have Python 3.7+ installed on Linux/MacOS/{ref}`Windows <jina-on-windows>`.

    ````{tab} via PyPI
    ```shell
    pip install -U jina
    ```
    ````
    ````{tab} via Conda
    ```shell
    conda install jina -c conda-forge
    ```
    ````
    ````{tab} via Docker
    ```shell
    docker pull jinaai/jina:latest
    ```
    ````

2. That’s it!
   ````{tab} Run natively
   ```shell
   jina -v
   ```
   ````
   ````{tab} Run in Docker
   ```shell
   docker run jinaai/jina:latest -v
   ```
   ````

Now that you’re set up, let’s dive into more of how Jina works and how to build great apps.


```{include} ../README.md
:start-after: <!-- start support-pitch -->
:end-before: <!-- end support-pitch -->
```

```{toctree}
:caption: Get started
:hidden:

get-started/neural-search
get-started/what-is-jina
get-started/install/index
get-started/create-app
```

```{toctree}
:caption: User Guides
:hidden:

fundamentals/architecture-overview
fundamentals/executor/index
fundamentals/flow/index
fundamentals/clean-code
```

```{toctree}
:caption: How-to
:hidden:
how-to/deploy
how-to/executor
```


```{toctree}
:caption: Developer Reference
:hidden:
:maxdepth: 1

get-started/migrate
api
cli/index
proto/docs
Jina 2 Documentation <https://docs2.jina.ai/>
```


---
{ref}`genindex` | {ref}`modindex`


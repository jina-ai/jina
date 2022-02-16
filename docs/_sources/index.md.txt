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

2. That’s it! Try a hello-world demo
   ````{tab} Run natively
   ```shell
   jina hello fashion
   ```
   ````
   ````{tab} Run in Docker
   ```shell
   docker run -v "$(pwd)/j:/j" jinaai/jina:latest hello fashion --workdir /j && open j/demo.html
   ```
   ````

Now that you’re set up, let’s dive into more of how Jina works and how to build great apps.

## Next steps

:::::{grid} 2
:gutter: 3


::::{grid-item-card} {octicon}`smiley;1.5em` Play 3 Hello World
:link: get-started/hello-world/index
:link-type: doc

Try Jina on fashion image search, QA chatbot and multimodal search.

::::

::::{grid-item-card} {octicon}`workflow;1.5em` Understand the Architecture 
:link: fundamentals/architecture-overview
:link-type: doc

Executor and Flow are the fundamental concepts in Jina.

::::

::::{grid-item-card} {octicon}`light-bulb;1.5em` Create a Jina Project
:link: get-started/create-app
:link-type: doc

Create a new Jina project with one line in the terminal
::::

::::{grid-item-card} {octicon}`package-dependents;1.5em` Share Executors
:link: fundamentals/executor/hub/index
:link-type: doc
:class-card: color-gradient-card

Learn to share and reuse Executors from the Jina community.
::::


:::::

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
get-started/hello-world/index
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
```


---
{ref}`genindex` | {ref}`modindex`


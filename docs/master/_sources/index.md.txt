# Welcome to Jina!

```{include} ../README.md
:start-after: <!-- start elevator-pitch -->
:end-before: <!-- end elevator-pitch -->
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

::::{grid-item-card} {octicon}`book;1.5em` Understand Basics
:link: fundamentals/concepts
:link-type: doc

Document, Executor, and Flow are the three fundamental concepts in Jina.

::::

::::{grid-item-card} {octicon}`infinity;1.5em` Tasks on Multi Data Types
:link: datatype/text/index
:link-type: doc
:class-card: color-gradient-card

Learn to use Jina to build neural search solution for different types of data.
::::

::::{grid-item-card} {octicon}`package-dependents;1.5em` Share Executors
:link: advanced/hub/index
:link-type: doc

Learn to share and reuse Executors from the Jina community.

::::


::::{grid-item-card} {octicon}`workflow;1.5em`  Manage Remote Jina 
:link: advanced/daemon/index
:link-type: doc

Learn to deploy and manage Jina on remote via a RESTful interface.
::::




::::{grid-item-card} {octicon}`beaker;1.5em` Try Experimental Features
:link: advanced/experimental/index
:link-type: doc

Preview the next big things we are building. Careful not to get zapped!
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
get-started/install/index
get-started/hello-world/index
```

```{toctree}
:caption: Fundamentals
:hidden:

fundamentals/concepts
fundamentals/document/index
fundamentals/executor/index
fundamentals/flow/index
fundamentals/clean-code
```


```{toctree}
:caption: Data Types
:hidden:

datatype/text/index
datatype/image/index
datatype/video/index
datatype/audio/index
datatype/mesh/index
datatype/tabular/index
```

```{toctree}
:caption: Advanced
:hidden:

advanced/hub/index
advanced/daemon/index
advanced/experimental/index
```


```{toctree}
:caption: API Reference
:hidden:
:maxdepth: 1

api/jina
cli/index
proto/index
```


---
{ref}`genindex` | {ref}`modindex`


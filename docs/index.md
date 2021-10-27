# Welcome to Jina!

```{include} ../README.md
:start-after: <!-- start elevator-pitch -->
:end-before: <!-- end elevator-pitch -->
```

## Install

1. Make sure that you have Python 3.7+ installed on Linux/MacOS/{ref}`Windows <jina-on-windows>`.
2. Install Jina

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
    docker run jinaai/jina:latest
    ```
    ````

3. Run hello-world demo
   ```bash 
   jina hello fashion
   ```
4. That’s it! In the next few seconds the demo will open in a new page in your browser.

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

::::{grid-item-card} {octicon}`package-dependents;1.5em` Share Executors
:link: advanced/hub/index
:link-type: doc

Learn how to share and reuse Executors from community.

::::


::::{grid-item-card} {octicon}`workflow;1.5em`  Manage Remote Jina 
:link: advanced/daemon/index
:link-type: doc

Learn how to deploy and manage Jina on remote via a RESTful interface.
::::


::::{grid-item-card} {octicon}`thumbsup;1.5em` Clean & Efficient Code 
:link: fundamentals/clean-code
:link-type: doc

Write beautiful & lean code with Jina.
::::

::::{grid-item-card} {octicon}`beaker;1.5em` Try Experimental Features
:link: advanced/experimental/index
:link-type: doc

Preview the next big thing we are building. Careful, zapping!
::::

::::{grid-item-card} {octicon}`gift;1.5em` Get Yourself Jina Swag
:link: https://jina.ai/blog/swag/

Awesome Jina swag to our awesome contributors (aka you)!
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
get-started/install
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
:caption: Data Type
:hidden:

datatype/text/index
datatype/image/index
datatype/video/index
datatype/audio/index
datatype/mesh/index
```

```{toctree}
:caption: Advanced
:hidden:

advanced/hub/index
advanced/master-executor
advanced/daemon/index
advanced/experimental/index
advanced/gpu-executor
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


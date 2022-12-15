# Welcome to Jina!

```{include} ../README.md
:start-after: <!-- start jina-description -->
:end-before: <!-- end jina-description -->
```

## Install

Make sure that you have Python 3.7+ installed on Linux/MacOS/{ref}`Windows <jina-on-windows>`.

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

Now that you’re set up, let’s create a project:

````{tab} In host
```shell
jina new hello-jina
cd hello-jina
jina flow --uses flow.yml
```
````
````{tab} Inside Docker
```shell
docker run -it --entrypoint=/bin/bash jinaai/jina:latest -p 54321:54321
jina new hello-jina
cd hello-jina
jina flow --uses flow.yml
```
````

Run the client on your machine and observe the results from your terminal.

```shell
python client.py
['hello, world!', 'goodbye, world!']
```


## Next steps

:::::{grid} 2
:gutter: 3


::::{grid-item-card} {octicon}`cross-reference;1.5em` Learn DocArray API
:link: https://docarray.jina.ai

DocArray is the foundational data structure of Jina. Before starting Jina, first learn DocArray to quickly build a PoC. 
::::

::::{grid-item-card} {octicon}`gear;1.5em` Understand Executor
:link: fundamentals/executor/index
:link-type: doc

{term}`Executor` is a self-contained logic unit that performs a group of tasks on a `DocumentArray`.

::::

::::{grid-item-card} {octicon}`workflow;1.5em` Understand Flow
:link: fundamentals/flow/index
:link-type: doc


{term}`Flow` orchestrates Executors into a processing pipeline to build a multi-modal/cross-modal application
::::

::::{grid-item-card} {octicon}`package-dependents;1.5em` Explore Jina Hub
:link: fundamentals/executor/hub/index
:link-type: doc
:class-card: color-gradient-card-1


Jina Hub is an Executor marketplace that allows you to share, explore and test Executors.

::::


::::{grid-item-card} {octicon}`cpu;1.5em` Deploy a Flow to JCloud
:link: fundamentals/jcloud/index
:link-type: doc
:class-card: color-gradient-card-2

JCloud is a free CPU/GPU hosting platform for Jina projects.
::::




::::{grid-item-card} {octicon}`squirrel;1.5em` Read in-depth tutorials
:link: how-to/index
:link-type: doc

Check out more in-depth tutorials on the advanced usages of Jina.
::::


:::::

```{include} ../README.md
:start-after: <!-- start support-pitch -->
:end-before: <!-- end support-pitch -->
```

```{toctree}
:caption: Introduction
:hidden:

get-started/what-is-cross-modal-multi-modal
get-started/what-is-jina
get-started/comparing-alternatives
```

```{toctree}
:caption: Get Started
:hidden:

get-started/install/index
get-started/create-app
```

```{toctree}
:caption: User Guides
:hidden:

fundamentals/architecture-overview
fundamentals/executor/index
fundamentals/flow/index
fundamentals/gateway/index
fundamentals/client/client
fundamentals/executor/hub/index
fundamentals/jcloud/index
how-to/index
```



```{toctree}
:caption: Developer Reference
:hidden:
:maxdepth: 1


api-rst
cli/index
yaml-spec
proto/docs
envs/index
telemetry
```

```{toctree}
:caption: Legacy Support
:hidden:
:maxdepth: 1

get-started/migrate
Jina 2 Documentation <https://docs2.jina.ai/>
```


---
{ref}`genindex` | {ref}`modindex`


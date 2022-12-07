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

::::{grid-item-card} {octicon}`gear;1.5em` Learn Executor
:link: concepts/executor/index
:link-type: doc

{term}`Executor` is a self-contained logic unit that performs a group of tasks on a `DocumentArray`.

::::

::::{grid-item-card} {octicon}`workflow;1.5em` Learn Flow
:link: concepts/flow/index
:link-type: doc


{term}`Flow` orchestrates Executors into a processing pipeline to accomplish a task.
::::

::::{grid-item-card} {octicon}`package-dependents;1.5em` Explore Executor Hub
:link: concepts/executor/hub/index
:link-type: doc
:class-card: color-gradient-card-1


Executor Hub is a marketplace that allows you to share, explore and test Executors.

::::


::::{grid-item-card} {octicon}`cpu;1.5em` Deploy a Flow to Cloud
:link: concepts/jcloud/index
:link-type: doc
:class-card: color-gradient-card-2

Jina AI Cloud is the MLOps platform for hosting Jina projects.
::::



:::::

```{include} ../README.md
:start-after: <!-- start support-pitch -->
:end-before: <!-- end support-pitch -->
```


```{toctree}
:caption: Get Started
:hidden:

get-started/install/index
get-started/create-app
```

```{toctree}
:caption: Concepts
:hidden:

concepts/preliminaries/index
concepts/executor/index
concepts/flow/index
concepts/gateway/index
concepts/client/index
```

```{toctree}
:caption: Cloud Native
:hidden:

cloud-nativeness/k8s
cloud-nativeness/docker-compose
cloud-nativeness/opentelemetry
jina-ai-cloud/index
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


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

Now that you’re set up, let’s dive into more of how Jina works and how to build great apps.


```{include} ../README.md
:start-after: <!-- start support-pitch -->
:end-before: <!-- end support-pitch -->
```

```{toctree}
:caption: Get Started
:hidden:

get-started/install/index
get-started/create-app
fundamentals/architecture-overview
```

```{toctree}
:caption: User Guides
:hidden:

fundamentals/executor/index
fundamentals/flow/index
fundamentals/gateway/index
fundamentals/flow/client
fundamentals/executor/hub/index
fundamentals/jcloud/index
how-to/index
```



```{toctree}
:caption: Developer References
:hidden:
:maxdepth: 1

api
cli/index
proto/docs
envs/index
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


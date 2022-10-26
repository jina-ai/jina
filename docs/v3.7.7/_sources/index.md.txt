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

```{important}

Telemetry is the process of collecting data about the usage of a system. This data can be used to improve the system by understanding how it is being used and what areas need improvement.

Jina uses telemetry to collect data about how the software is being used. This data is then used to improve the software. For example, if Jina sees that a lot of users are having trouble with a certain feature, they can improve that feature to make it easier to use.

Telemetry is important for Jina because it allows the team to understand how the software is being used and what areas need improvement. Without telemetry, Jina would not be able to improve as quickly or as effectively.

The data collected include:

- Jina and its dependencies versions;
- A hashed unique user identifier;
- A hashed unique session identifie;r
- Boolean events: start of a Flow, Gateway and Runtime.

```

```{tip}
If you'd like to opt out of usage statistics, make sure to add the `--optout-telemetry` argument to the different Flows and Executors or set the `JINA_OPTOUT_TELEMETRY=1` environment variable.

```


```{toctree}
:caption: Get Started
:hidden:

get-started/what-is
get-started/why-jina
fundamentals/architecture-overview
get-started/install/index
get-started/create-app
```

```{toctree}
:caption: User Guides
:hidden:

fundamentals/executor/index
fundamentals/flow/index
fundamentals/gateway/index
fundamentals/client/client
fundamentals/executor/hub/index
fundamentals/jcloud/index
how-to/index
```



```{toctree}
:caption: Developer References
:hidden:
:maxdepth: 1


api-rst
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


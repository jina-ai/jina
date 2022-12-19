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

````{tab} Natively on the host
```shell
jina new hello-jina && jina flow --uses hello-jina/flow.yml
```
````
````{tab} In a Docker container
```shell
docker run jinaai/jina:latest -v "$(pwd)/j:/j" new hello-jina
docker run -v "$(pwd)/j:/j" -p 54321:54321 jinaai/jina:latest flow --uses /j/hello-jina/flow.yml
```
````

Run the client on your machine and observe the results from your terminal.

````{tab} via gRPC in Python
```python
from jina import Client, DocumentArray

c = Client(host='grpc://0.0.0.0:54321')
da = c.post('/', DocumentArray.empty(2))
print(da.texts)
```
````
````{tab} via HTTP in Python
```python
from jina import Client, DocumentArray

c = Client(host='http://0.0.0.0:54322')
da = c.post('/', DocumentArray.empty(2))
print(da.texts)
```
````
````{tab} via WebSocket in Python
```python
from jina import Client, DocumentArray

c = Client(host='ws://0.0.0.0:54323')
da = c.post('/', DocumentArray.empty(2))
print(da.texts)
```
````
````{tab} via HTTP using Javascript
```javascript
fetch('http://localhost:54322/post', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: {}
}).then(response => response.json()).then(data => console.log(data));
```
````
````{tab} via HTTP using curl
```bash
curl --request POST 'http://localhost:54323/post' --header 'Content-Type: application/json' -d '{}'
```
````



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
concepts/preliminaries/index
```

```{toctree}
:caption: Concepts
:hidden:

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
envs/index
telemetry
proto/docs
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


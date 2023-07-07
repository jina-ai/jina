<p align="center">
<!-- survey banner start -->
<a href="https://10sw1tcpld4.typeform.com/to/EGAEReM7?utm_source=readme&utm_medium=github&utm_campaign=user%20experience&utm_term=feb2023&utm_content=survey">
  <img src="./.github/banner.svg?raw=true">
</a>
<!-- survey banner start -->

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/docs/_static/logo-light.svg?raw=true" alt="Jina logo: Build multimodal AI services via cloud native technologies · Neural Search · Generative AI · Cloud Native" width="150px"></a>
</p>

<p align="center">
<b>Build multimodal AI services with cloud native technologies</b>
</p>

<p align=center>
<a href="https://pypi.org/project/jina/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jina?label=Release&style=flat-square"></a>
<!--<a href="https://codecov.io/gh/jina-ai/jina"><img alt="Codecov branch" src="https://img.shields.io/codecov/c/github/jina-ai/jina/master?&logo=Codecov&logoColor=white&style=flat-square"></a>-->
<a href="https://discord.jina.ai"><img src="https://img.shields.io/discord/1106542220112302130?logo=discord&logoColor=white&style=flat-square"></a>
<a href="https://pypistats.org/packages/jina"><img alt="PyPI - Downloads from official pypistats" src="https://img.shields.io/pypi/dm/jina?style=flat-square"></a>
<a href="https://github.com/jina-ai/jina/actions/workflows/cd.yml"><img alt="Github CD status" src="https://github.com/jina-ai/jina/actions/workflows/cd.yml/badge.svg"></a>
</p>

<!-- start jina-description -->

Jina lets you build multimodal [**AI services**](#build-ai-services) and [**pipelines**](#build-a-pipeline) that communicate via gRPC, HTTP and WebSockets, then scale them up and deploy to production. You can focus on your logic and algorithms, without worrying about the infrastructure complexity.

![](./.github/images/build-deploy.png)

Jina provides a smooth Pythonic experience transitioning from local deployment to advanced orchestration frameworks like Docker-Compose, Kubernetes, or Jina AI Cloud. Jina makes advanced solution engineering and cloud-native technologies accessible to every developer.

- Build applications for any [data type](https://docs.docarray.org/data_types/first_steps/), any mainstream [deep learning framework](), and any [protocol](https://docs.jina.ai/concepts/serving/gateway/#set-protocol-in-python).
- Design high-performance microservices, with [easy scaling](https://docs.jina.ai/concepts/orchestration/scale-out/), duplex client-server streaming, and async/non-blocking data processing over dynamic flows.
- Docker container integration via [Executor Hub](https://cloud.jina.ai), OpenTelemetry/Prometheus observability, and fast Kubernetes/Docker-Compose deployment.
- CPU/GPU hosting via [Jina AI Cloud](https://cloud.jina.ai).

<details>
    <summary><strong>Wait, how is Jina different from FastAPI?</strong></summary>
Jina's value proposition may seem quite similar to that of FastAPI. However, there are several fundamental differences:

 **Data structure and communication protocols**
  - FastAPI communication relies on Pydantic and Jina relies on [DocArray](https://github.com/docarray/docarray) allowing Jina to support multiple protocols
  to expose its services.

 **Advanced orchestration and scaling capabilities**
  - Jina lets you deploy applications formed from multiple microservices that can be containerized and scaled independently.
  - Jina allows you to easily containerize and orchestrate your services, providing concurrency and scalability.

 **Journey to the cloud**
  - Jina provides a smooth transition from local development (using [DocArray](https://github.com/docarray/docarray)) to local serving using (Jina's orchestration layer)
  to having production-ready services by using Kubernetes capacity to orchestrate the lifetime of containers.
  - By using [Jina AI Cloud](https://cloud.jina.ai) you have access to scalable and serverless deployments of your applications in one command.
</details>

<!-- end jina-description -->

## [Documentation](https://docs.jina.ai)

## Install 

```bash
pip install jina
```

Find more install options on [Apple Silicon](https://docs.jina.ai/get-started/install/apple-silicon-m1-m2/)/[Windows](https://docs.jina.ai/get-started/install/windows/).

## Get Started

### Basic Concepts

Jina has three fundamental layers:

- Data layer: [**BaseDoc**](https://docarray.docs.org/) and [**DocList**](https://docarray.docs.org/) (from [DocArray](https://github.com/docarray/docarray)) is the input/output format in Jina.
- Serving layer: An [**Executor**](https://docs.jina.ai/concepts/serving/executor/) is a Python class that transforms and processes Documents. [**Gateway**](https://docs.jina.ai/concepts/serving/gateway/) is the service making sure connecting all Executors inside a Flow.
- Orchestration layer:  [**Deployment**](https://docs.jina.ai/concepts/orchestration/deployment) serves a single Executor, while a [**Flow**](https://docs.jina.ai/concepts/orchestration/flow/) serves Executors chained into a pipeline.


[The full glossary is explained here](https://docs.jina.ai/concepts/preliminaries/#).

### Build AI Services
<!-- start build-ai-services -->

Let's build a fast, reliable and scalable gRPC-based AI service. In Jina we call this an **[Executor](https://docs.jina.ai/concepts/serving/executor/)**. Our simple Executor will wrap the [StableLM](https://huggingface.co/stabilityai/stablelm-base-alpha-3b) LLM from Stability AI. We'll then use a **Deployment** to serve it.

![](./.github/images/deployment-diagram.png)

> **Note**
> A Deployment serves just one Executor. To combine multiple Executors into a pipeline and serve that, use a [Flow](#build-a-pipeline).

Let's implement the service's logic:

<table>
<tr>
<th><code>executor.py</code></th> 
<tr>
<td>

```python
from jina import Executor, requests
from docarray import DocList, BaseDoc

from transformers import pipeline


class Prompt(BaseDoc):
    text: str


class Generation(BaseDoc):
    prompt: str
    text: str


class StableLM(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generator = pipeline(
            'text-generation', model='stabilityai/stablelm-base-alpha-3b'
        )

    @requests
    def generate(self, docs: DocList[Prompt], **kwargs) -> DocList[Generation]:
        generations = DocList[Generation]()
        prompts = docs.text
        llm_outputs = self.generator(prompts)
        for prompt, output in zip(prompts, llm_outputs):
            generations.append(Generation(prompt=prompt, text=output))
        return generations

```

</td>
</tr>
</table>

Then we deploy it with either the Python API or YAML:
<div class="table-wrapper">
<table>
<tr>
<th> Python API: <code>deployment.py</code> </th> 
<th> YAML: <code>deployment.yml</code> </th>
</tr>
<tr>
<td>

```python
from jina import Deployment
from executor import StableLM

dep = Deployment(uses=StableLM, timeout_ready=-1, port=12345)

with dep:
    dep.block()
```

</td>
<td>

```yaml
jtype: Deployment
with:
  uses: StableLM
  py_modules:
    - executor.py
  timeout_ready: -1
  port: 12345
```

And run the YAML Deployment with the CLI: `jina deployment --uses deployment.yml`

</td>
</tr>
</table>
</div>

Use [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the service:

```python
from jina import Client
from docarray import DocList, BaseDoc


class Prompt(BaseDoc):
    text: str


class Generation(BaseDoc):
    prompt: str
    text: str


prompt = Prompt(
    text='suggest an interesting image generation prompt for a mona lisa variant'
)

client = Client(port=12345)  # use port from output above
response = client.post(on='/', inputs=[prompt], return_type=DocList[Generation])

print(response[0].text)
```

```text
a steampunk version of the Mona Lisa, incorporating mechanical gears, brass elements, and Victorian era clothing details
```

<!-- end build-ai-services -->

> **Note**
> In a notebook, you can't use `deployment.block()` and then make requests to the client. Please refer to the Colab link above for reproducible Jupyter Notebook code snippets.

### Build a pipeline

<!-- start build-pipelines -->

Sometimes you want to chain microservices together into a pipeline. That's where a [Flow](https://docs.jina.ai/concepts/orchestration/flow/) comes in.

A Flow is a [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) pipeline, composed of a set of steps, It orchestrates a set of [Executors](https://docs.jina.ai/concepts/serving/executor/) and a [Gateway](https://docs.jina.ai/concepts/serving/gateway/) to offer an end-to-end service.

> **Note**
> If you just want to serve a single Executor, you can use a [Deployment](#build-ai--ml-services).

For instance, let's combine [our StableLM language model](#build-ai--ml-services) with a Stable Diffusion image generation service. Chaining these services together into a [Flow](https://docs.jina.ai/concepts/orchestration/flow/) will give us a service that will generate images based on a prompt generated by the LLM.


<table>
<tr>
<th><code>text_to_image.py</code></th> 
<tr>
<td>

```python
import numpy as np
from jina import Executor, requests
from docarray import BaseDoc, DocList
from docarray.documents import ImageDoc


class Generation(BaseDoc):
    prompt: str
    text: str


class TextToImage(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from diffusers import StableDiffusionPipeline
        import torch

        self.pipe = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4", torch_dtype=torch.float16
        ).to("cuda")

    @requests
    def generate_image(self, docs: DocList[Generation], **kwargs) -> DocList[ImageDoc]:
        images = self.pipe(
            docs.text
        ).images  # image here is in [PIL format](https://pillow.readthedocs.io/en/stable/)
        docs.tensor = np.array(images)
```

</td>
</tr>
</table>


![](./.github/images/flow-diagram.png)

Build the Flow with either Python or YAML:

<div class="table-wrapper">
<table>
<tr>
<th> Python API: <code>flow.py</code> </th> 
<th> YAML: <code>flow.yml</code> </th>
</tr>
<tr>
<td>

```python
from jina import Flow
from executor import StableLM
from text_to_image import TextToImage

flow = (
    Flow(port=12345)
    .add(uses=StableLM, timeout_ready=-1)
    .add(uses=TextToImage, timeout_ready=-1)
)

with flow:
    flow.block()
```

</td>
<td>

```yaml
jtype: Flow
with:
    port: 12345
executors:
  - uses: StableLM
    timeout_ready: -1
    py_modules:
      - executor.py
  - uses: TextToImage
    timeout_ready: -1
    py_modules:
      - text_to_image.py
```

Then run the YAML Flow with the CLI: `jina flow --uses flow.yml`

</td>
</tr>
</table>
</div>

Then, use [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the Flow:

```python
from jina import Client
from docarray import DocList, BaseDoc
from docarray.documents import ImageDoc


class Prompt(BaseDoc):
    text: str


prompt = Prompt(
    text='suggest an interesting image generation prompt for a mona lisa variant'
)

client = Client(port=12345)  # use port from output above
response = client.post(on='/', inputs=[prompt], return_type=DocList[ImageDoc])

response[0].display()
```

![](./.github/images/mona-lisa.png)

<!-- end build-pipelines -->

### Easy scalability and concurrency

Why not just use standard Python to build that microservice and pipeline? Jina accelerates time to market of your application by making it more scalable and cloud-native. Jina also handles the infrastructure complexity in production and other Day-2 operations so that you can focus on the data application itself.

Increase your application's throughput with scalability features out of the box, like [replicas](https://docs.jina.ai/concepts/orchestration/scale-out/#replicate-executors), [shards](https://docs.jina.ai/concepts/orchestration/scale-out/#customize-polling-behaviors) and [dynamic batching](https://docs.jina.ai/concepts/serving/executor/dynamic-batching/).

Let's scale a Stable Diffusion Executor deployment with replicas and dynamic batching:

![](./.github/images/scaled-deployment.png)

* Create two replicas, with [a GPU assigned for each](https://docs.jina.ai/concepts/orchestration/scale-out/#replicate-on-multiple-gpus).
* Enable dynamic batching to process incoming parallel requests together with the same model inference.


<div class="table-wrapper">
<table>
<tr>
<th> Normal Deployment </th> 
<th> Scaled Deployment </th>
</tr>
<tr>
<td>

```yaml
jtype: Deployment
with:
  uses: TextToImage
  timeout_ready: -1
  py_modules:
    - text_to_image.py
```

</td>
<td>

```yaml
jtype: Deployment
with:
  uses: TextToImage
  timeout_ready: -1
  py_modules:
    - text_to_image.py
  env:
   CUDA_VISIBLE_DEVICES: RR
  replicas: 2
  uses_dynamic_batching: # configure dynamic batching
    /default:
      preferred_batch_size: 10
      timeout: 200
```

</td>
</tr>
</table>
</div>

Assuming your machine has two GPUs, using the scaled deployment YAML will give better throughput compared to the normal deployment.

These features apply to both [Deployment YAML](https://docs.jina.ai/concepts/orchestration/yaml-spec/#example-yaml) and [Flow YAML](https://docs.jina.ai/concepts/orchestration/yaml-spec/#example-yaml). Thanks to the YAML syntax, you can inject deployment configurations regardless of Executor code.

## Deploy to the cloud

### Containerize your Executor

In order to deploy your solutions to the cloud, you need to containerize your services. Jina provides the [Executor Hub](https://docs.jina.ai/concepts/serving/executor/hub/create-hub-executor/), the perfect tool
to streamline this process taking a lot of the troubles with you. It also lets you share these Executors publicly or privately.

You just need to structure your Executor in a folder:

```shell script
TextToImage/
├── executor.py
├── config.yml
├── requirements.txt
```
<div class="table-wrapper">
<table>
<tr>
<th> <code>config.yml</code> </th>
<th> <code>requirements.txt</code> </th>
</tr>
<tr>
<td>

```yaml
jtype: TextToImage
py_modules:
  - executor.py
metas:
  name: TextToImage
  description: Text to Image generation Executor based on StableDiffusion
  url:
  keywords: []
```

</td>
<td>

```requirements.txt
diffusers
accelerate
transformers
```

</td>
</tr>
</table>
</div>


Then push the Executor to the Hub by doing: `jina hub push TextToImage`.

This will give you a URL that you can use in your `Deployment` and `Flow` to use the pushed Executors containers.


```yaml
jtype: Flow
with:
    port: 12345
executors:
  - uses: jinai+docker://<user-id>/StableLM
  - uses: jinai+docker://<user-id>/TextToImage
```


### Get on the fast lane to cloud-native

Using Kubernetes with Jina is easy:

```bash
jina export kubernetes flow.yml ./my-k8s
kubectl apply -R -f my-k8s
```

And so is Docker Compose:

```bash
jina export docker-compose flow.yml docker-compose.yml
docker-compose up
```

> **Note**
> You can also export Deployment YAML to [Kubernetes](https://docs.jina.ai/concepts/serving/executor/serve/#serve-via-kubernetes) and [Docker Compose](https://docs.jina.ai/concepts/serving/executor/serve/#serve-via-docker-compose).

That's not all. We also support [OpenTelemetry, Prometheus, and Jaeger](https://docs.jina.ai/cloud-nativeness/opentelemetry/).

What cloud-native technology is still challenging to you? [Tell us](https://github.com/jina-ai/jina/issues) and we'll handle the complexity and make it easy for you.

### Deploy to JCloud

You can also deploy a Flow to JCloud, where you can easily enjoy autoscaling, monitoring and more with a single command. 

First, turn the `flow.yml` file into a [JCloud-compatible YAML](https://docs.jina.ai/yaml-spec/) by specifying resource requirements and using containerized Hub Executors.

Then, use `jina cloud deploy` command to deploy to the cloud:

```shell
wget https://raw.githubusercontent.com/jina-ai/jina/master/.github/getting-started/jcloud-flow.yml
jina cloud deploy jcloud-flow.yml
```

> **Warning**
>
> Make sure to delete/clean up the Flow once you are done with this tutorial to save resources and credits.

Read more about [deploying Flows to JCloud](https://docs.jina.ai/concepts/jcloud/#deploy).

<!-- start support-pitch -->

## Support

- Join our [Discord community](https://discord.jina.ai) and chat with other community members about ideas.
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE).

<!-- end support-pitch -->

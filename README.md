<p align="center">
<!-- survey banner start -->
<a href="https://10sw1tcpld4.typeform.com/to/EGAEReM7?utm_source=readme&utm_medium=github&utm_campaign=user%20experience&utm_term=feb2023&utm_content=survey">
  <img src="./.github/banner.svg?raw=true">
</a>
<!-- survey banner start -->

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/docs/_static/logo-light.svg?raw=true" alt="Jina logo: Build multimodal AI services via cloud native technologies · Neural Search · Generative AI · Cloud Native" width="150px"></a>
<br><br><br>
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

Jina is an MLOps framework to build multimodal AI microservice-based applications written in Python that can communicate via gRPC, HTTP and WebSocket protocols.
It allows developers to build and serve **services** and **pipelines** while **scaling** and **deploying** them to a production while removing the complexity, letting them focus on the 
logic/algorithmic part, saving valuable time and resources for engineering teams.

Jina aims to provide a smooth Pythonic experience transitioning from local deployment to deploying to advanced orchestration frameworks such as Docker-Compose, Kubernetes, or Jina AI Cloud.
It handles the infrastructure complexity, making advanced solution engineering and cloud-native technologies accessible to every developer.

<p align="center">
<strong><a href="#build-ai-services">Build and deploy a gRPC microservice</a> • <a href="#build-a-pipeline">Build and deploy a pipeline</a></strong>
</p>

Applications built with Jina enjoy the following features out of the box:

🌌 **Universal**
  - Build applications that deliver fresh insights from multiple data types such as text, image, audio, video, 3D mesh, PDF with [LF's DocArray](https://github.com/docarray/docarray).
  - Support for all mainstream deep learning frameworks.
  - Polyglot gateway that supports gRPC, Websockets, HTTP, GraphQL protocols with TLS.

⚡ **Performance**
  - Intuitive design pattern for high-performance microservices.
  - Easy scaling: set replicas, sharding in one line. 
  - Duplex streaming between client and server.
  - Async and non-blocking data processing over dynamic flows.

☁️ **Cloud native**
  - Seamless Docker container integration: sharing, exploring, sandboxing, versioning and dependency control via [Executor Hub](https://cloud.jina.ai).
  - Full observability via OpenTelemetry and Prometheus.
  - Fast deployment to Kubernetes and Docker Compose.

🍱 **Ecosystem**
  - Improved engineering efficiency thanks to the Jina AI ecosystem, so you can focus on innovating with the data applications you build.
  - Free CPU/GPU hosting via [Jina AI Cloud](https://cloud.jina.ai).

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

<!-- end jina-description -->

## [Documentation](https://docs.jina.ai)

## Install 

```bash
pip install jina
```

Find more install options on [Apple Silicon](https://docs.jina.ai/get-started/install/apple-silicon-m1-m2/)/[Windows](https://docs.jina.ai/get-started/install/windows/).

## Get Started

### Basic Concepts

Jina has four fundamental concepts:

- A [**Document**](https://docarray.jina.ai/) (from [DocArray](https://github.com/docarray/docarray)) is the input/output format in Jina.
- An [**Executor**](https://docs.jina.ai/concepts/serving/executor/) is a Python class that transforms and processes Documents.
- A [**Deployment**](https://docs.jina.ai/concepts/orchestration/deployment) serves a single Executor, while a [**Flow**](https://docs.jina.ai/concepts/orchestration/flow/) serves Executors chained into a pipeline.

[The full glossary is explained here](https://docs.jina.ai/concepts/preliminaries/#).

---

### Build AI Services
<!-- start build-ai-services -->

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jina/blob/master/.github/getting-started/notebook.ipynb)

Let's build a fast, reliable and scalable gRPC-based AI service. In Jina we call this an **[Executor](https://docs.jina.ai/concepts/executor/)**. Our simple Executor will use Facebook's mBART-50 model to translate French to English. We'll then use a **Deployment** to serve it.

> **Note**
> A Deployment serves just one Executor. To combine multiple Executors into a pipeline and serve that, use a [Flow](#build-a-pipeline).

> **Note**
> Run the [code in Colab](https://colab.research.google.com/github/jina-ai/jina/blob/master/.github/getting-started/notebook.ipynb#scrollTo=0l-lkmz4H-jW) to install all dependencies.

Let's implement the service's logic:

<table>
<tr>
<th><code>translate_executor.py</code> </th> 
<tr>
<td>

```python
from docarray import DocumentArray
from jina import Executor, requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class Translator(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt", src_lang="fr_XX"
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt"
        )

    @requests
    def translate(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = self._translate(doc.text)

    def _translate(self, text):
        encoded_en = self.tokenizer(text, return_tensors="pt")
        generated_tokens = self.model.generate(
            **encoded_en, forced_bos_token_id=self.tokenizer.lang_code_to_id["en_XX"]
        )
        return self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[
            0
        ]
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
from translate_executor import Translator

with Deployment(uses=Translator, timeout_ready=-1) as dep:
    dep.block()
```

</td>
<td>

```yaml
jtype: Deployment
with:
  uses: Translator
  py_modules:
    - translate_executor.py # name of the module containing Translator
  timeout_ready: -1
```

And run the YAML Deployment with the CLI: `jina deployment --uses deployment.yml`

</td>
</tr>
</table>
</div>

```text
──────────────────────────────────────── 🎉 Deployment is ready to serve! ─────────────────────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓      Protocol                   GRPC │
│  🏠        Local          0.0.0.0:12345  │
│  🔒      Private      172.28.0.12:12345  │
│  🌍       Public    35.230.97.208:12345  │
╰──────────────────────────────────────────╯
```

Use [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the service:

```python
from docarray import Document
from jina import Client

french_text = Document(
    text='un astronaut est en train de faire une promenade dans un parc'
)

client = Client(port=12345)  # use port from output above
response = client.post(on='/', inputs=[french_text])

print(response[0].text)
```

```text
an astronaut is walking in a park
```

<!-- end build-ai-services -->

> **Note**
> In a notebook, one cannot use `deployment.block()` and then make requests to the client. Please refer to the colab link above for reproducible Jupyter Notebook code snippets.


### Build a pipeline

<!-- start build-pipelines -->
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jina/blob/master/.github/getting-started/notebook.ipynb#scrollTo=YfNm1nScH30U)

Sometimes you want to chain microservices together into a pipeline. That's where a [Flow](https://docs.jina.ai/concepts/flow/) comes in.

A Flow is a [DAG](https://de.wikipedia.org/wiki/DAG) pipeline, composed of a set of steps, It orchestrates a set of [Executors](https://docs.jina.ai/concepts/executor/) and a [Gateway](https://docs.jina.ai/concepts/gateway/) to offer an end-to-end service.

> **Note**
> If you just want to serve a single Executor, you can use a [Deployment](#build-ai--ml-services).

For instance, let's combine [our French translation service](#build-ai--ml-services) with a Stable Diffusion image generation service from Jina AI's [Executor Hub](https://cloud.jina.ai/executors). Chaining these services together into a [Flow](https://docs.jina.ai/concepts/flow/) will give us a multilingual image generation service.

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

flow = (
    Flow()
    .add(uses=Translator, timeout_ready=-1)
    .add(
        uses='jinaai://jina-ai/TextToImage',
        timeout_ready=-1,
        install_requirements=True,
    )
)  # use the Executor from Executor hub

with flow:
    flow.block()
```

</td>
<td>

```yaml
jtype: Flow
executors:
  - uses: Translator
    timeout_ready: -1
    py_modules:
      - translate_executor.py
  - uses: jinaai://jina-ai/TextToImage
    timeout_ready: -1
    install_requirements: true
```

Then run the YAML Flow with the CLI: `jina flow --uses flow.yml`

</td>
</tr>
</table>
</div>

```text
─────────────────────────────────────────── 🎉 Flow is ready to serve! ────────────────────────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓      Protocol                   GRPC  │
│  🏠        Local          0.0.0.0:12345  │
│  🔒      Private      172.28.0.12:12345  │
│  🌍       Public    35.240.201.66:12345  │
╰──────────────────────────────────────────╯
```

Then, use [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the Flow:

```python
from jina import Client, Document

client = Client(port=12345)  # use port from output above

french_text = Document(
    text='un astronaut est en train de faire une promenade dans un parc'
)

response = client.post(on='/', inputs=[french_text])

response[0].display()
```


![stable-diffusion-output.png](https://raw.githubusercontent.com/jina-ai/jina/master/.github/stable-diffusion-output.png)


You can also deploy a Flow to JCloud.

First, turn the `flow.yml` file into a [JCloud-compatible YAML](https://docs.jina.ai/concepts/jcloud/yaml-spec/) by specifying resource requirements and using containerized Hub Executors.

Then, use `jina cloud deploy` command to deploy to the cloud:


```shell
wget https://raw.githubusercontent.com/jina-ai/jina/master/.github/getting-started/jcloud-flow.yml
jina cloud deploy jcloud-flow.yml
```

⚠️ **Caution: Make sure to delete/clean up the Flow once you are done with this tutorial to save resources and credits.**

Read more about [deploying Flows to JCloud](https://docs.jina.ai/concepts/jcloud/#deploy).

<!-- end build-pipelines -->

Check [the getting-started project source code](https://github.com/jina-ai/jina/tree/master/.github/getting-started).

---

Why not just use standard Python to build that microservice and pipeline? Jina accelerates time to market of your application by making it more scalable and cloud-native. Jina also handles the infrastructure complexity in production and other Day-2 operations so that you can focus on the data application itself.

### Easy scalability and concurrency

Increase your application's throughput with scalability features out of the box, like [replicas](https://docs.jina.ai/concepts/orchestration/scale-out/#replicate-executors), [shards](https://docs.jina.ai/concepts/orchestration/scale-out/#customize-polling-behaviors) and [dynamic batching](https://docs.jina.ai/concepts/serving/executor/dynamic-batching/).

Let's scale a Stable Diffusion Executor deployment with replicas and dynamic batching:

* Create two replicas, with [a GPU assigned for each](https://docs.jina.ai/concepts/flow/scale-out/#replicate-on-multiple-gpus).
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
  timeout_ready: -1
  uses: jinaai://jina-ai/TextToImage
  install_requirements: true
```

</td>
<td>

```yaml
jtype: Deployment
with:
  timeout_ready: -1
  uses: jinaai://jina-ai/TextToImage
  install_requirements: true
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

These features apply to both [Deployment YAML](https://docs.jina.ai/concepts/executor/deployment-yaml-spec/#deployment-yaml-spec) and [Flow YAML](https://docs.jina.ai/concepts/flow/yaml-spec/). Thanks to the YAML syntax, you can inject deployment configurations regardless of Executor code.

---

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
> You can also export Deployment YAML to [Kubernetes](https://docs.jina.ai/concepts/executor/serve/#serve-via-kubernetes) and [Docker Compose](https://docs.jina.ai/concepts/executor/serve/#serve-via-docker-compose).

That's not all. We also support [OpenTelemetry, Prometheus, and Jaeger](https://docs.jina.ai/cloud-nativeness/opentelemetry/).

What cloud-native technology is still challenging to you? [Tell us](https://github.com/jina-ai/jina/issues) and we'll handle the complexity and make it easy for you.

<!-- start support-pitch -->

## Support

- Join our [Discord community](https://discord.jina.ai) and chat with other community members about ideas.
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE).

<!-- end support-pitch -->

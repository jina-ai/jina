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
<b>Build multimodal AI services via cloud native technologies</b>
</p>


<p align=center>
<a href="https://pypi.org/project/jina/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jina?label=Release&style=flat-square"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img alt="Codecov branch" src="https://img.shields.io/codecov/c/github/jina-ai/jina/master?&logo=Codecov&logoColor=white&style=flat-square"></a>
<a href="https://jina.ai/slack"><img src="https://img.shields.io/badge/Slack-3.6k-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
<a href="https://pypistats.org/packages/jina"><img alt="PyPI - Downloads from official pypistats" src="https://img.shields.io/pypi/dm/jina?style=flat-square"></a>
<a href="https://github.com/jina-ai/jina/actions/workflows/cd.yml"><img alt="Github CD status" src="https://github.com/jina-ai/jina/actions/workflows/cd.yml/badge.svg"></a>
</p>

<!-- start jina-description -->

Jina is an MLOps framework to build multimodal AI **services** and **pipelines**. Use Jina to **serve** and **scale** AI services and **deploy** them to a production-ready environment like Kubernetes or Jina AI Cloud. Jina handles the infrastructure complexity, making advanced solution engineering and cloud-native technologies accessible to every developer.

Use cases:
* [Build and deploy a gRPC microservice](#build-ai--ml-services)
* [Deploy and deploy a pipeline](#build-a-pipeline)

Applications built with Jina enjoy the following features out of the box:

🌌 **Universal**
  - Build applications that deliver fresh insights from multiple data types such as text, image, audio, video, 3D mesh, PDF with [LF's DocArray](https://github.com/docarray/docarray).
  - Support all mainstream deep learning frameworks.
  - Polyglot gateway that supports gRPC, Websockets, HTTP, GraphQL protocols with TLS.

⚡ **Performance**
  - Intuitive design pattern for high-performance microservices.
  - Scaling at ease: set replicas, sharding in one line. 
  - Duplex streaming between client and server.
  - Async and non-blocking data processing over dynamic flows.

☁️ **Cloud native**
  - Seamless Docker container integration: sharing, exploring, sandboxing, versioning and dependency control via [Executor Hub](https://cloud.jina.ai).
  - Full observability via OpenTelemetry, Prometheus and Grafana.
  - Fast deployment to Kubernetes, Docker Compose.

🍱 **Ecosystem**
  - Improved engineering efficiency thanks to the Jina AI ecosystem, so you can focus on innovating with the data applications you build.
  - Free CPU/GPU hosting via [Jina AI Cloud](https://cloud.jina.ai).

<!-- end jina-description -->

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/core-tree-graph.svg?raw=true" alt="Jina in Jina AI neural search ecosystem" width="100%"></a>
</p>




## [Documentation](https://docs.jina.ai)

## Install 

```bash
pip install jina
```

Find more install options on [Apple Silicon](https://docs.jina.ai/get-started/install/apple-silicon-m1-m2/)/[Windows](https://docs.jina.ai/get-started/install/windows/).


## Get Started


### Basic Concepts

Document, Executor and Flow are three fundamental concepts in Jina.

- [**Document**](https://docarray.jina.ai/) from [DocArray](https://github.com/docarray/docarray) is the fundamental data structure behind data validation and serialization.
- [**Executor**](https://docs.jina.ai/concepts/executor/) is a Python class that can serve logic using Documents.
- [**Flow**](https://docs.jina.ai/concepts/flow/) and [**Deployment**](https://docs.jina.ai/concepts/executor/serve/#serve-directly) orchestrates Executors into standalone services or pipelines.

[The full glossary is explained here.](https://docs.jina.ai/concepts/preliminaries/#)


---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/streamline-banner.png?raw=true" alt="Jina: Streamline AI & ML Product Delivery" width="100%"></a>
</p>

### Build AI & ML Services
<!-- start build-ai-services -->
<!-- TODO: change to master before merging -->
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jina/blob/docs-readme-changes/.github/getting-started/notebook.ipynb)

Build fast, reliable and scalable gRPC-based AI services with Jina.

Start by installing the dependencies:
```shell
pip install jina transformers==4.26.1 sentencepiece==0.1.97 torch==1.13.1 protobuf==3.19.6
```

Then implement a translation service logic with [Executor](https://docs.jina.ai/concepts/executor/) in `translate_executor.py`:
```python
from jina import Executor, requests, DocumentArray
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

Then serve it either with the Python API or YAML:
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

with Deployment(uses=Translator, port=12345, timeout_ready=-1) as dep:
    dep.block()
```

</td>
<td>

```yaml
jtype: Deployment
with:
  port: 12345
  uses: Translator
  py_modules:
    - translate_executor.py # name of the module containing Translator
  timeout_ready: -1
```
And run the YAML Deployemt with the CLI: `jina deployment --uses deployment.yml`

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

And use [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the service:
```python
from jina import Client, Document

client = Client(port=12345)
docs = client.post(
    on='/',
    inputs=[
        Document(text='un astronaut est en train de faire une promenade dans un parc')
    ],
)
print(docs[0].text)
```

```text
an astronaut is walking in a park
```

<!-- end build-ai-services -->

### Build a pipeline


<!-- start build-pipelines -->
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jina-ai/jina/blob/docs-readme-changes/.github/getting-started/notebook.ipynb)

In case your solution can be modeled as a [DAG](https://de.wikipedia.org/wiki/DAG) pipeline, composed of a set of tasks, 
use Jina [Flow](https://docs.jina.ai/concepts/flow/).
It orchestrates a set of [Executors](https://docs.jina.ai/concepts/executor/) and a [Gateway](https://docs.jina.ai/concepts/gateway/) to offer an end-to-end service.

For instance, let's combine the French translation service with a Stable Diffusion image generation service from [Jina Hub](https://cloud.jina.ai/executors).
Chaining such services with [Flow](https://docs.jina.ai/concepts/flow/) will give us a multilingual image generation service.

Use the Flow either with the Python API or YAML:

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
    Flow(port=12345)
    .add(uses=Translator, timeout_ready=-1)
    .add(
        uses='jinaai://alaeddineabdessalem/TextToImage',
        timeout_ready=-1,
        install_requirements=True,
    )
)  # use the Executor from jina hub

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
  - uses: Translator
    timeout_ready: -1
    py_modules:
      - translate_executor.py
  - uses: jinaai://alaeddineabdessalem/TextToImage
    timeout_ready: -1
    install_requirements: true

```

And run the YAML Flow with the CLI: `jina flow --uses flow.yml`
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

Then, use the [Jina Client](https://docs.jina.ai/concepts/client/) to make requests to the Flow:

```python
from jina import Client, Document

client = Client(port=12345)

docs = client.post(
    on='/',
    inputs=[
        Document(text='un astronaut est en train de faire une promenade dans un parc')
    ],
)
docs[0].display()
```

<!-- TODO: replace with master later -->

![stable-diffusion-output.png](https://raw.githubusercontent.com/jina-ai/jina/docs-readme-changes/.github/stable-diffusion-output.png)

<!-- TODO: uncomment later -->

<!-- 
You can also deploy such a pipeline to JCloud.
First, turn the `flow.yml` file into a [jcloud-compatible YAML](https://docs.jina.ai/concepts/jcloud/yaml-spec/) by specifying resource requirements and using containerized Hub Executors.

Then, use `jina cloud deploy` command to deploy to the cloud:
(TODO: replace wit master later)
```shell
wget https://raw.githubusercontent.com/jina-ai/jina/docs-readme-changes/.github/getting-started/jcloud-flow.yml
jina cloud deploy jcloud-flow.yml
```

Read more about [deploying Flows to JCloud](https://docs.jina.ai/concepts/jcloud/#deploy).
 -->

<!-- end build-pipelines -->

Check [the getting-started project source code](https://github.com/jina-ai/jina/tree/master/.github/getting-started).

---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/no-complexity-banner.png?raw=true" alt="Jina: No Infrastructure Complexity, High Engineering Efficiency" width="100%"></a>
</p>


While you could use standard Python with the same number of lines and get the same output, Jina accelerates time to market of your application by making it more scalable and cloud-native. Jina also handles the infrastructure complexity in production and other Day-2 operations so that you can focus on the data application itself.


---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/scalability-banner.png?raw=true" alt="Jina: Scalability and concurrency at ease" width="100%"></a>
</p>

### Scalability and concurrency at ease

Let's take the following example:

<table>
<tr>
<th> <code>toy.yml</code> </th> 
<th> executor.py </th>
</tr>
<tr>
<td> 

```yaml
jtype: Flow
with:
  port: 51000
  protocol: grpc
executors:
- uses: MyExec
  name: foo
  py_modules:
    - executor.py
- uses: MyExec
  name: bar
  py_modules:
    - executor.py
```
     
</td>
<td>

```python
from jina import DocumentArray, Executor, requests


class MyExec(Executor):
    @requests
    async def add_text(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'hello, world!'
```

</td>
</tr>
</table>


Run the following command in the terminal:

```bash
jina flow --uses toy.yml
```

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/flow-block.png?raw=true" alt="Running a simple hello-world program" width="50%"></a>
</p>

The server is successfully started, and you can now use a client to query it.

```python
from jina import Client, Document

c = Client(host='grpc://0.0.0.0:51000')
c.post('/', Document())
```

The separation of Flow YAML and Executor Python file does not only make the project more maintainable but also brings scalability and concurrency to the next level:
- The data flow on the server is non-blocking and async. New request is handled immediately when an Executor is free, regardless if previous request is still being processed.
- Scalability can be easily achieved by the keywords `replicas` and `needs` in YAML/Python. Load-balancing is automatically added when necessary to ensure the maximum throughput.

<table>
<tr>
<th> <code>toy.yml</code> </th> 
<th> Flowchart </th>
</tr>
<tr>
<td> 

```yaml
jtype: Flow
with:
  port: 51000
  protocol: grpc
executors:
- uses: MyExec
  name: foo
  py_modules:
    - executor.py
  replicas: 2
- uses: MyExec
  name: bar
  py_modules:
    - executor.py
  replicas: 3
  needs: gateway
- needs: [foo, bar]
  name: baz
```
     
</td>
<td>

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/scale-flow.svg?raw=true" alt="Running a simple hello-world program" width="70%"></a>
</p>

</td>
</tr>
</table>

- You now have an API gateway that supports gRPC (default), Websockets, and HTTP protocols with TLS.
- The communication between clients and the API gateway is duplex.
- The API gateway allows you to route request to a specific Executor while other parts of the Flow are still busy, via `.post(..., target_executor=...)`

---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/container-banner.png?raw=true" alt="Jina: Seamless Container Integration" width="100%"></a>
</p>

### Seamless Container integration

Without having to worry about dependencies, you can easily share your Executors with others; or use public/private Executors in your project thanks to [Executor Hub](https://cloud.jina.ai).

To create an Executor:

```bash
jina hub new 
```

To push it to Executor Hub:

```bash
jina hub push .
```

To use a Hub Executor in your Flow:

|        | Docker container                           | Sandbox                                     | Source                              |
|--------|--------------------------------------------|---------------------------------------------|-------------------------------------|
| YAML   | `uses: jinaai+docker://<username>/MyExecutor`        | `uses: jinaai+sandbox://<username>/MyExecutor`        | `uses: jinaai://<username>/MyExecutor`        |
| Python | `.add(uses='jinaai+docker://<username>/MyExecutor')` | `.add(uses='jinaai+sandbox://<username>/MyExecutor')` | `.add(uses='jinaai://<username>/MyExecutor')` |

Behind this smooth experience is advanced management of Executors:
- Automated builds on the cloud
- Store, deploy, and deliver Executors cost-efficiently;
- Automatically resolve version conflicts and dependencies;
- Instant delivery of any Executor via Sandbox without pulling anything to local.

---

<p align="center">
<a href="https://docs.jina.ai"><img src=".github/readme/cloud-native-banner.png?raw=true" alt="Jina: Seamless Container Integration" width="100%"></a>
</p>

### Fast-lane to cloud-native

Using Kubernetes becomes easy:

```bash
jina export kubernetes flow.yml ./my-k8s
kubectl apply -R -f my-k8s
```

Using Docker Compose becomes easy:

```bash
jina export docker-compose flow.yml docker-compose.yml
docker-compose up
```

P.S: you can also export Deployment YAML to [Kubernetes](https://docs.jina.ai/concepts/executor/serve/#serve-via-kubernetes) and [Docker Compose](https://docs.jina.ai/concepts/executor/serve/#serve-via-docker-compose).

Tracing and monitoring with OpenTelemetry is straightforward:

```python
from jina import Executor, requests, DocumentArray


class MyExec(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        with self.tracer.start_as_current_span(
            'encode', context=tracing_context
        ) as span:
            with self.monitor(
                'preprocessing_seconds', 'Time preprocessing the requests'
            ):
                docs.tensors = preprocessing(docs)
            with self.monitor(
                'model_inference_seconds', 'Time doing inference the requests'
            ):
                docs.embedding = model_inference(docs.tensors)
```

You can integrate Jaeger or any other distributed tracing tools to collect and visualize request-level and application level service operation attributes. This helps you analyze request-response lifecycle, application behavior and performance.

To use Grafana, [download this JSON](https://github.com/jina-ai/example-grafana-prometheus/blob/main/grafana-dashboards/flow-histogram-metrics.json) and import it into Grafana:

<p align="center">
<a href="https://docs.jina.ai"><img src=".github/readme/grafana-histogram-metrics.png?raw=true" alt="Jina: Seamless Container Integration" width="70%"></a>
</p>

To trace requests with Jaeger:
<p align="center">
<a href="https://docs.jina.ai"><img src=".github/readme/jaeger-tracing-example.png?raw=true" alt="Jina: Seamless Container Integration" width="70%"></a>
</p>


What cloud-native technology is still challenging to you? [Tell us](https://github.com/jina-ai/jina/issues), we will handle the complexity and make it easy for you.

<!-- start support-pitch -->

## Support

- Join our [Slack community](https://jina.ai/slack) and chat with other community members about ideas.
- Join our [Engineering All Hands](https://youtube.com/playlist?list=PL3UBBWOUVhFYRUa_gpYYKBqEAkO4sxmne) meet-up to discuss your use case and learn Jina's new features.
    - **When?** The second Tuesday of every month
    - **Where?**
      Zoom ([see our public events calendar](https://calendar.google.com/calendar/embed?src=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&ctz=Europe%2FBerlin)/[.ical](https://calendar.google.com/calendar/ical/c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com/public/basic.ics))
      and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE).

<!-- end support-pitch -->

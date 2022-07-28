<p align="center">
<br><br><br>
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/docs/_static/logo-light.svg?raw=true" alt="Jina logo: Build cross-modal and multi-modal applications on the cloud" width="150px"></a>
<br><br><br>
</p>

<p align="center">
<b>Build cross-modal and multi-modal applications on the cloud</b>
</p>


<p align=center>
<a href="https://pypi.org/project/jina/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jina?label=Release&style=flat-square"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img alt="Codecov branch" src="https://img.shields.io/codecov/c/github/jina-ai/jina/master?&logo=Codecov&logoColor=white&style=flat-square"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-3.1k-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
<a href="https://github.com/jina-ai/jina/actions/workflows/cd.yml"><img alt="Github CD status" src="https://github.com/jina-ai/jina/actions/workflows/cd.yml/badge.svg"></a>
</p>

<!-- start jina-description -->

Jina is a framework that empowers anyone to build cross-modal and multi-modal<sup><a href="#example-application">[*]</a></sup> applications on the cloud. It uplifts a PoC into a production-ready service. Jina handles the infrastructure complexity, making advanced solution engineering and cloud-native technologies accessible to every developer. 

<sub><sup><a id="example-application">[*]</a> Example cross-modal application: <a href="https://github.com/jina-ai/discoart/">DiscoArt</a>, <a href="https://github.com/jina-ai/dalle-flow/">DALL·E Flow</a>; example multi-modal services: <a href="https://github.com/jina-ai/clip-as-service/">CLIP-as-service</a>, <a href="https://github.com/jina-ai/now/">Jina Now</a>.</sup></sub>

Applications built with Jina enjoy the following features out-of-the-box:

🌌 **Universal**
  - Build applications that deliver fresh insights from multiple data types such as text, image, audio, video, 3D mesh, PDF with [Jina AI's DocArray](https://docarray.jina.ai).
  - Support all mainstream deep learning frameworks.
  - Polyglot gateway that supports gRPC, Websockets, HTTP, GraphQL protocols with TLS.

⚡ **Performance**
  - Intuitive design pattern for high-performance microservices.
  - Scaling at ease: set replicas, sharding in one line. 
  - Duplex streaming between client and server.
  - Async and non-blocking data processing over dynamic flows.

☁️ **Cloud-native**
  - Seamless Docker container integration: sharing, exploring, sandboxing, versioning and dependency control via [Jina Hub](https://hub.jina.ai).
  - Fast deployment to Kubernetes, Docker Compose and [Jina Cloud](https://docs.jina.ai/fundamentals/jcloud/).
  - Full observability via Prometheus and Grafana.

🍱 **Ecosystem**
  - Improved engineering efficiency thanks to the Jina AI ecosystem, so you can focus on innovating with the data applications you build.

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/core-tree-graph.svg?raw=true" alt="Jina in Jina AI neural search ecosystem" width="100%"></a>
</p>

<!-- end jina-description -->

## [Documentation](https://docs.jina.ai)

## Install 

```bash
pip install jina
```

[More install options can be found in the docs](https://docs.jina.ai/get-started/install/).


## Get Started


### Basic Concepts

Document, Executor and Flow are three fundamental concepts in Jina.

- [**Document**](https://docarray.jina.ai/) is the fundamental data structure.
- [**Executor**](https://docs.jina.ai/fundamentals/executor/) is a Python class with functions that use Documents as IO.
- [**Flow**](https://docs.jina.ai/fundamentals/flow/) ties Executors together into a pipeline and exposes it with an API gateway.

[The full glossary is explained here.](https://docs.jina.ai/fundamentals/architecture-overview/)

---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/no-complexity-banner.png?raw=true" alt="Jina: No Infrastructure Complexity, High Engineering Efficiency" width="100%"></a>
</p>

### Hello world example

Leveraging these three concepts, let's look at a simple example below:

```python
from jina import DocumentArray, Executor, Flow, requests


class MyExec(Executor):
    @requests
    async def add_text(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'hello, world!'


f = Flow().add(uses=MyExec).add(uses=MyExec)

with f:
    r = f.post('/', DocumentArray.empty(2))
    print(r.texts)
```

- The first line imports three concepts we just introduced;
- `MyExec` defines an async function `add_text` that receives `DocumentArray` from network requests and appends `"hello, world"` to `.text`;
- `f` defines a Flow streamlined two Executors in a chain;
- The `with` block opens the Flow, sends an empty DocumentArray to the Flow, and prints the result.

Running it gives you:

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/run-hello-world.gif?raw=true" alt="Running a simple hello-world program" width="70%"></a>
</p>

At the last line we see its output `['hello, world!hello, world!', 'hello, world!hello, world!']`.


While one could use standard Python with the same number of lines and get the same output, Jina accelerates time to market of your application by making it more scalable and cloud-native. Jina also handles the infrastructure complexity in production and other Day-2 operations so that you can focus on the data application itself.  

---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/scalability-banner.png?raw=true" alt="Jina: Scalability and concurrency at ease" width="100%"></a>
</p>

### Scalability and concurrency at ease

The example above can be refactored into a Python Executor file and a Flow YAML file:

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

This simple refactoring allows developers to write an application in the client-server style. The separation of Flow YAML and Executor Python file does not only make the project more maintainable but also brings scalability and concurrency to the next level:
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

Without having to worry about dependencies, you can easily share your Executors with others; or use public/private Executors in your project thanks to [Jina Hub](https://hub.jina.ai).

To create an Executor:

```bash
jina hub new 
```

To push it to Jina Hub:

```bash
jina hub push .
```

To use a Hub Executor in your Flow:

|        | Docker container                           | Sandbox                                     | Source                              |
|--------|--------------------------------------------|---------------------------------------------|-------------------------------------|
| YAML   | `uses: jinahub+docker://MyExecutor`        | `uses: jinahub+sandbox://MyExecutor`        | `uses: jinahub://MyExecutor`        |
| Python | `.add(uses='jinahub+docker://MyExecutor')` | `.add(uses='jinahub+sandbox://MyExecutor')` | `.add(uses='jinahub://MyExecutor')` |

Behind this smooth experience is advanced management of Executors:
- Automated builds on the cloud
- Store, deploy, and deliver Executors cost-efficiently;
- Automatically resolve version conflicts and dependencies;
- Instant delivery of any Executor via Sandbox without pulling anything to local.

---

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/cloud-native-banner.png?raw=true" alt="Jina: Seamless Container Integration" width="100%"></a>
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

Using Prometheus becomes easy:

```python
from jina import Executor, requests, DocumentArray


class MyExec(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        with self.monitor('preprocessing_seconds', 'Time preprocessing the requests'):
            docs.tensors = preprocessing(docs)
        with self.monitor(
            'model_inference_seconds', 'Time doing inference the requests'
        ):
            docs.embedding = model_inference(docs.tensors)
```

Using Grafana becomes easy, just [download this JSON](https://github.com/jina-ai/example-grafana-prometheus/blob/main/grafana-dashboards/flow.json) and import it into Grafana:

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/grafana.png?raw=true" alt="Jina: Seamless Container Integration" width="70%"></a>
</p>


What cloud-native technology is still challenging to you? [Tell us](https://github.com/jina-ai/jina/issues), we will handle the complexity and make it easy for you.

<!-- start support-pitch -->

## Support

- Join our [Slack community](https://slack.jina.ai) and chat with other community members about ideas.
- Join our [Engineering All Hands](https://youtube.com/playlist?list=PL3UBBWOUVhFYRUa_gpYYKBqEAkO4sxmne) meet-up to discuss your use case and learn Jina's new features.
    - **When?** The second Tuesday of every month
    - **Where?**
      Zoom ([see our public events calendar](https://calendar.google.com/calendar/embed?src=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&ctz=Europe%2FBerlin)/[.ical](https://calendar.google.com/calendar/ical/c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com/public/basic.ics))
      and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE).
[We are actively hiring](https://jobs.jina.ai) AI engineers, solution engineers to build the next neural search ecosystem in open source.

<!-- end support-pitch -->

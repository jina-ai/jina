<p align="center">
<br><br><br>
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/docs/_static/logo-light.svg?raw=true" alt="Jina logo: Build cross-modal and multi-modal applications on the cloud" width="150px"></a>
<br><br><br>
</p>

<p align="center">
<b>Build cross-modal and multi-modal applications on the cloud</b>
</p>


<p align=center>
<a href="https://github.com/jina-ai/jina/actions/workflows/cd.yml"><img alt="Github CD status" src="https://github.com/jina-ai/jina/actions/workflows/cd.yml/badge.svg"></a>
<a href="https://pypi.org/project/jina/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jina?label=PyPI&logo=pypi&logoColor=white&style=flat-square"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img alt="Codecov branch" src="https://img.shields.io/codecov/c/github/jina-ai/jina/master?logo=Codecov&logoColor=white&style=flat-square"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-3.0k-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
</p>

<!-- start jina-description -->

Jina is a framework that empowers anyone to build cross-modal and multi-modal<sup><a href="#example-application">[*]</a></sup> applications on the cloud. It uplifts a PoC into a production-ready service in just minutes. Jina handles the infrastructure complexity, making advanced solution engineering and cloud-native technologies accessible to every developer. 

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
  - Seamless Docker integration: sharing, exploring, sandboxing, versioning and dependency control via [Jina Hub](https://hub.jina.ai).
  - Fast deployment to Kubernetes, Docker Compose and Jina Cloud.
  - Full observability via Prometheus and Grafana.

🍱 **Ecosystem**
  - Improved engineering efficiency thanks to the Jina AI ecosystem, so you can focus on innovating with the data applications you build.

<sup><a id="example-application">[*]</a> Example cross-modal application: <a href="https://github.com/jina-ai/dalle-flow/">DALL·E Flow</a>; example multi-modal services: <a href="https://github.com/jina-ai/clip-as-service/">CLIP-as-service</a>, <a href="https://github.com/jina-ai/now/">Jina Now</a>.</sup>

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
- [**Executor**](https://docs.jina.ai/fundamentals/executor/) is a group of functions with Documents as IO.
- [**Flow**](https://docs.jina.ai/fundamentals/flow/) ties Executors together into a pipeline and exposes it with an API gateway.


<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/no-complexity-banner.png?raw=true" alt="Jina: No Infrastructure Complexity, High Engineering Efficiency" width="100%"></a>
</p>

### Hello world example

Leveraging these three concepts, let's look at a simple example below:

```python
from jina import DocumentArray, Executor, Flow, requests


class MyExec(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'hello, world!'


f = Flow().add(uses=MyExec).add(uses=MyExec)

with f:
    r = f.post('/', DocumentArray.empty(2))
    print(r.texts)
```

- The first line imports three concepts we just introduced;
- `MyExec` defines an async function `foo` that receives `DocumentArray` from network requests and appends `"hello, world"` to `.text`;
- `f` defines a Flow streamlined two Executors in a chain;
- The `with` block opens the Flow, sends an empty DocumentArray to the Flow, and prints the result.

Running it gives you:

<p align="center">
<a href="#"><img src="https://github.com/jina-ai/jina/blob/master/.github/readme/run-hello-world.gif?raw=true" alt="Running a simple hello-world program" width="70%"></a>
</p>

At the last line we see its output `['hello, world!hello, world!', 'hello, world!hello, world!']`.


While one could use standard Python with the same number of lines and get the same output, Jina accelerates time to market of your application by making it more scalable and cloud-native. Jina also handles the infrastructure complexity in production and other Day-2 operations so that you can focus on the data application itself.  

### Scalability and concurrency at ease

tba

### Seamless Docker integration

tba

### Fast-lane to cloud-native

tba



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

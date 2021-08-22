<p align="center">
<!-- <a href="https://www.meetup.com/jina-community-meetup/events/279360997/"><img src="https://github.com/jina-ai/jina/blob/master/.github/images/meetup.svg"></a> -->
<a href="https://jina.ai/"><img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina logo: Jina is a cloud-native neural search framework" width="200px"></a>
</p>

<p align="center">
<b>Cloud-Native <ins>Neural Search</ins><sup><a href=".github/2.0/neural-search.md">[?]</a></sup> Framework for <i>Any</i> Kind of Data</b>
</p>


<p align=center>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://pepy.tech/project/jina"><img src="https://pepy.tech/badge/jina/month"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img src="https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg" alt="codecov"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-900%2B-blueviolet?logo=slack&amp;logoColor=white"></a>
</p>

<!-- start elevator-pitch -->

Jina<sup><a href=".github/pronounce-jina.mp3">`🔊`</a></sup> allows you to build search-as-a-service powered by deep learning in just minutes.

<!-- end elevator-pitch -->

🌌 **All data types** - Large-scale indexing and querying of any kind of unstructured data: video, image, long/short text, music, source code, PDF, etc.

🌩️ **Fast & cloud-native** - Distributed architecture from day one, scalable & cloud-native by design: enjoy
containerizing, streaming, paralleling, sharding, async scheduling, HTTP/gRPC/WebSocket protocol.

⏱️ **Save time** - *The* design pattern of neural search systems, from zero to a production-ready system in minutes.

🍱 **Own your stack** - Keep end-to-end stack ownership of your solution, avoid integration pitfalls you get with
fragmented, multi-vendor, generic legacy tools.



## Run Quick Demo

- [👗 Fashion image search](./.github/pages/hello-world.md#-fashion-image-search): `jina hello fashion`
- [🤖 QA chatbot](./.github/pages/hello-world.md#-covid-19-chatbot): `pip install "jina[demo]" && jina hello chatbot`
- [📰 Multimodal search](./.github/pages/hello-world.md#-multimodal-document-search): `pip install "jina[demo]" && jina hello multimodal`
- 🍴 Fork the source of a demo to your folder: `jina hello fork fashion ../my-proj/`

## Install

- via PyPI: `pip install -U jina`
- via Docker: `docker run jinaai/jina:latest`

<details>
<summary>More installation options</summary>

| On x86/64, arm64/v6/v7 | Linux/macOS with Python 3.7/3.8/3.9 | Docker Users |
| --- | --- | --- |
| Minimum <br>(no HTTP, WebSocket, Docker support) | `JINA_PIP_INSTALL_CORE=1 pip install jina` | `docker run jinaai/jina:latest` |
| Minimum but more performant <br>(use `uvloop` & `lz4`) | `JINA_PIP_INSTALL_PERF=1 pip install jina` | `docker run jinaai/jina:latest-perf` |
| With <a href="https://api.jina.ai/daemon/">Daemon</a> | `pip install "jina[daemon]"` | [Run JinaD](.github/2.0/cookbooks/Daemon.md#run) |
| Full development dependencies | `pip install "jina[devel]"` | `docker run jinaai/jina:latest-devel` |
| Pre-release<br>(all tags above can be added)| <sub>`pip install --pre jina` | `docker run jinaai/jina:master` |


Version identifiers [are explained here](https://github.com/jina-ai/jina/blob/master/RELEASE.md). Jina can run
on [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community
to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

</details>

## Get Started

Document, Executor, and Flow are the three fundamental concepts in Jina.

- [📄 **Document**](.github/2.0/cookbooks/Document.md) is the basic data type in Jina;
- [⚙️ **Executor**](.github/2.0/cookbooks/Executor.md) is how Jina processes Documents;
- [🔀 **Flow**](.github/2.0/cookbooks/Flow.md) is how Jina streamlines and distributes Executors.

1️⃣ Copy-paste the minimum example below and run it:

<sup>💡 Preliminaries: <a href="https://en.wikipedia.org/wiki/Word_embedding">character embedding</a>, <a href="https://computersciencewiki.org/index.php/Max-pooling_/_Pooling">pooling</a>, <a href="https://en.wikipedia.org/wiki/Euclidean_distance">Euclidean distance</a></sup>

<img src="https://github.com/jina-ai/jina/blob/master/.github/2.0/simple-arch.svg" alt="The architecture of a simple neural search system powered by Jina">

<!-- README-SERVER-START -->
```python
import numpy as np
from jina import Document, DocumentArray, Executor, Flow, requests

class CharEmbed(Executor):  # a simple character embedding with mean-pooling
    offset = 32  # letter `a`
    dim = 127 - offset + 1  # last pos reserved for `UNK`
    char_embd = np.eye(dim) * 1  # one-hot embedding for all chars

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1) for c in d.text]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling

class Indexer(Executor):
    _docs = DocumentArray()  # for storing all documents in memory

    @requests(on='/index')
    def foo(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)  # extend stored `docs`

    @requests(on='/search')
    def bar(self, docs: DocumentArray, **kwargs):
         docs.match(self._docs, metric='euclidean', limit=20)

f = Flow(port_expose=12345, protocol='http', cors=True).add(uses=CharEmbed, parallel=2).add(uses=Indexer)  # build a Flow, with 2 parallel CharEmbed, tho unnecessary
with f:
    f.post('/index', (Document(text=t.strip()) for t in open(__file__) if t.strip()))  # index all lines of _this_ file
    f.block()  # block for listening request
```
<!-- README-SERVER-END -->

2️⃣ Open `http://localhost:12345/docs` (an extended Swagger UI) in your browser, click <kbd>/search</kbd> tab and input:

```json
{"data": [{"text": "@requests(on=something)"}]}
```

That means, **we want to find lines from the above code snippet that are most similar to `@request(on=something)`.**  Now click <kbd>Execute</kbd> button!

<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/swagger-ui-prettyprint1.gif?raw=true" alt="Jina Swagger UI extension on visualizing neural search results" width="85%">
</p>

3️⃣ Not a GUI person? Let's do it in Python then! Keep the above server running and start a simple client:


<!-- README-CLIENT-START -->
```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["euclidean"].value:2f}: "{d.text}"')


c = Client(protocol='http', port_expose=12345)  # connect to localhost:12345
c.post('/search', Document(text='request(on=something)'), on_done=print_matches)
```

<!-- README-CLIENT-END -->

, which prints the following results:

```text
         Client@1608[S]:connected to the gateway at localhost:12345!
[0]0.168526: "@requests(on='/index')"
[1]0.181676: "@requests(on='/search')"
[2]0.192049: "query.matches = [Document(self._docs[int(idx)], copy=True, score=d) for idx, d in enumerate(dist)]"
```
<sup>😔 Doesn't work? Our bad! <a href="https://github.com/jina-ai/jina/issues/new?assignees=&labels=kind%2Fbug&template=---found-a-bug-and-i-solved-it.md&title=">Please report it here.</a></sup>


## Read Tutorials

- 🧠 [What is "Neural Search"?](.github/2.0/neural-search.md)
- 📄 `Document` & `DocumentArray`: the basic data type in Jina.
    - [Minimum Working Example](.github/2.0/cookbooks/Document.md#minimum-working-example)
    - [`Document` API](.github/2.0/cookbooks/Document.md#document-api)
    - [`DocumentArray` API](.github/2.0/cookbooks/Document.md#documentarray-api)
    - [`DocumentArrayMemmap` API](.github/2.0/cookbooks/Document.md#documentarraymemmap-api)
- ⚙️ `Executor`: how Jina processes Documents.
    - [Minimum working example](.github/2.0/cookbooks/Executor.md#minimum-working-example)
    - [`Executor` API](.github/2.0/cookbooks/Executor.md#executor-api)
    - [`Executor` Built-in Features](.github/2.0/cookbooks/Executor.md#executor-built-in-features)
    - [Use Tensorflow, Pytorch, Pytorch Lightning, Fastai, Mindspore, PaddlePaddle, Scikit-learn in `Executor`](.github/2.0/cookbooks/Executor.md#executors-in-action)
- 🔀 `Flow`: how Jina streamlines and distributes Executors.
    - [Minimum Working Example](.github/2.0/cookbooks/Flow.md#minimum-working-example)
    - [`Flow` API](.github/2.0/cookbooks/Flow.md#flow-api)
- 🤹 Serving Jina as a Service
    - [Minimum Working Example](.github/2.0/cookbooks/Serving.md#minimum-working-example)
    - [`Flow`-as-a-Service](.github/2.0/cookbooks/Serving.md#flow-as-a-service)
    - [Deliver OAS3.0 Friendly API](.github/2.0/cookbooks/Serving.md#extend-http-interface)
- 👹️ `JinaD`: create & manage remote Jina Executors & Flows.
  - [Minimum Working Example](.github/2.0/cookbooks/Daemon.md#minimum-working-example)
  - [JinaD Server & Client](.github/2.0/cookbooks/Daemon.md#setup-jinad-server)
  - [Create Remote Executors](.github/2.0/cookbooks/Daemon.md#create-a-remote-executor)
  - [Create Remote Flows](.github/2.0/cookbooks/Daemon.md#create-remote-flows)
- 📓 [Developer Reference](https://docs.jina.ai)
- 🧼 [Clean & Efficient Coding in Jina](.github/2.0/cookbooks/CleanCode.md)
- 🚶‍ Walkthroughs
  - [How to Build Hello World Chatbot](https://jina.ai/blog/tutorial)
  - [Create Your Own Executor](https://jina.ai/blog/tutorial-executors)

    
## Support

- Join our [Slack community](https://slack.jina.ai) to chat to our engineers about your use cases, questions, and
  support queries.
- Join our [Engineering All Hands](https://youtube.com/playlist?list=PL3UBBWOUVhFYRUa_gpYYKBqEAkO4sxmne) meet-up to discuss your use case and learn Jina's new features.
    - **When?** The second Tuesday of every month
    - **Where?**
      Zoom ([see our public events calendar](https://calendar.google.com/calendar/embed?src=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&ctz=Europe%2FBerlin)/[.ical](https://calendar.google.com/calendar/ical/c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com/public/basic.ics))
      and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai). [We are actively hiring](https://jobs.jina.ai) full-stack developers,
solution engineers to build the next neural search ecosystem in open source.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to
your active involvement.

- [Release cycles and development stages](RELEASE.md)
- [Contributing guidelines](CONTRIBUTING.md)
- [Code of conduct](https://github.com/jina-ai/jina/blob/master/.github/CODE_OF_CONDUCT.md)
  community
- [Get yourself some swags](https://jina.ai/blog/swag)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-171-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="18px;"/></a> <a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="18px;"/></a> <a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="18px;"/></a> <a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="18px;"/></a> <a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="18px;"/></a> <a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="18px;"/></a> <a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="18px;"/></a> <a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/davidbp"><img src="https://avatars.githubusercontent.com/u/4223580?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mezig351"><img src="https://avatars.githubusercontent.com/u/10896185?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ApurvaMisra"><img src="https://avatars.githubusercontent.com/u/22544948?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/samjoy"><img src="https://avatars.githubusercontent.com/u/3750744?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/DARREN-ZHANG"><img src="https://avatars.githubusercontent.com/u/8371825?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bhavsarpratik"><img src="https://avatars.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Showtim3"><img src="https://avatars.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/anshulwadhawan"><img src="https://avatars.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/yk"><img src="https://avatars.githubusercontent.com/u/858040?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/atibaup"><img src="https://avatars.githubusercontent.com/u/1799897?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/deepampatel"><img src="https://avatars.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PabloRN"><img src="https://avatars.githubusercontent.com/u/727564?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/winstonww"><img src="https://avatars.githubusercontent.com/u/13983591?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/umbertogriffo"><img src="https://avatars.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/alasdairtran"><img src="https://avatars.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pswu11"><img src="https://avatars.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/makram93"><img src="https://avatars.githubusercontent.com/u/6537525?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kelton8Z"><img src="https://avatars.githubusercontent.com/u/22567795?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/janandreschweiger"><img src="https://avatars.githubusercontent.com/u/44372046?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Immich"><img src="https://avatars.githubusercontent.com/u/9353470?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Nishil07"><img src="https://avatars.githubusercontent.com/u/63183230?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mohamed--abdel-maksoud"><img src="https://avatars.githubusercontent.com/u/1863880?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/shakurshams"><img src="https://avatars.githubusercontent.com/u/67507873?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/fernandakawasaki"><img src="https://avatars.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="18px;"/></a> <a href="https://maateen.me/"><img src="https://avatars.githubusercontent.com/u/11742254?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/hongchhe"><img src="https://avatars.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="18px;"/></a> <a href="http://fayeah.github.io/"><img src="https://avatars.githubusercontent.com/u/29644978?v=4" class="avatar-user" width="18px;"/></a> <a href="http://willperkins.com/"><img src="https://avatars.githubusercontent.com/u/576702?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ThePfarrer"><img src="https://avatars.githubusercontent.com/u/7157861?v=4" class="avatar-user" width="18px;"/></a> <a href="https://cristianmtr.github.io/resume/"><img src="https://avatars.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/harry-stark"><img src="https://avatars.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/xinbin-huang/"><img src="https://avatars.githubusercontent.com/u/27927454?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Roshanjossey"><img src="https://avatars.githubusercontent.com/u/8488446?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/davidli-oneflick"><img src="https://avatars.githubusercontent.com/u/62926164?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/yuanb"><img src="https://avatars.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/qwe123coder"><img src="https://avatars.githubusercontent.com/u/72848513?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/lucia-loher/"><img src="https://avatars.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jyothishkjames"><img src="https://avatars.githubusercontent.com/u/937528?v=4" class="avatar-user" width="18px;"/></a> <a href="https://gitcommit.show/"><img src="https://avatars.githubusercontent.com/u/56937085?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/carlosbaezruiz/"><img src="https://avatars.githubusercontent.com/u/1107703?v=4" class="avatar-user" width="18px;"/></a> <a href="https://blog.lsgrep.com/"><img src="https://avatars.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/doomdabo"><img src="https://avatars.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/pgiank28"><img src="https://avatars.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="18px;"/></a> <a href="http://hargup.in/"><img src="https://avatars.githubusercontent.com/u/2477788?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rameshwara"><img src="https://avatars.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="18px;"/></a> <a href="https://shivaylamba.me/"><img src="https://avatars.githubusercontent.com/u/19529592?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadejsv"><img src="https://avatars.githubusercontent.com/u/11489772?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/RenrakuRunrat"><img src="https://avatars.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/kaushikb11"><img src="https://avatars.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pdaryamane"><img src="https://avatars.githubusercontent.com/u/11886076?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/uvipen"><img src="https://avatars.githubusercontent.com/u/47221207?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/smy0428"><img src="https://avatars.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/SirsikarAkshay"><img src="https://avatars.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="18px;"/></a> <a href="http://freesearch.pe.kr/"><img src="https://avatars.githubusercontent.com/u/957840?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bsmth"><img src="https://avatars.githubusercontent.com/u/43580235?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/properGrammar"><img src="https://avatars.githubusercontent.com/u/20957896?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jancijen"><img src="https://avatars.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/akurniawan25/"><img src="https://avatars.githubusercontent.com/u/4723643?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/serge-m"><img src="https://avatars.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/cpooley"><img src="https://avatars.githubusercontent.com/u/17229557?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sebastianlettner.info/"><img src="https://avatars.githubusercontent.com/u/51201318?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/kilianyp"><img src="https://avatars.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sridatta.ml/"><img src="https://avatars.githubusercontent.com/u/17333185?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jacobowitz"><img src="https://avatars.githubusercontent.com/u/6544965?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Gracegrx"><img src="https://avatars.githubusercontent.com/u/23142113?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/aga11313"><img src="https://avatars.githubusercontent.com/u/23415764?v=4" class="avatar-user" width="18px;"/></a> <a href="http://bit.ly/3qKM0uO"><img src="https://avatars.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="18px;"/></a> <a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/FionnD"><img src="https://avatars.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mapleeit"><img src="https://avatars.githubusercontent.com/u/4194287?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bsherifi"><img src="https://avatars.githubusercontent.com/u/32338617?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/MiaAltieri"><img src="https://avatars.githubusercontent.com/u/32723809?v=4" class="avatar-user" width="18px;"/></a> <a href="https://fb.com/saurabh.nemade"><img src="https://avatars.githubusercontent.com/u/17445338?v=4" class="avatar-user" width="18px;"/></a> <a href="https://prasakis.com/"><img src="https://avatars.githubusercontent.com/u/10392953?v=4" class="avatar-user" width="18px;"/></a> <a href="https://nech.pl/"><img src="https://avatars.githubusercontent.com/u/1821404?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ManudattaG"><img src="https://avatars.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://jakobkruse.com/"><img src="https://avatars.githubusercontent.com/u/42516008?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/LukeekuL"><img src="https://avatars.githubusercontent.com/u/24293913?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/strawberrypie"><img src="https://avatars.githubusercontent.com/u/29224443?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.milchior.fr/"><img src="https://avatars.githubusercontent.com/u/357361?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Yongxuanzhang"><img src="https://avatars.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/dalekatwork"><img src="https://avatars.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/innerNULL"><img src="https://avatars.githubusercontent.com/u/10429190?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JamesTang-616"><img src="https://avatars.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Arrrlex"><img src="https://avatars.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadej-redstone"><img src="https://avatars.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/niuzs-alan"><img src="https://avatars.githubusercontent.com/u/32271197?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bio-howard"><img src="https://avatars.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="18px;"/></a> <a href="https://jina.ai/"><img src="https://avatars.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/robertjrodger"><img src="https://avatars.githubusercontent.com/u/15660082?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/CatStark"><img src="https://avatars.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="18px;"/></a>
<a href="http://www.efho.de/"><img src="https://avatars.githubusercontent.com/u/6096895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/prabhupad-pradhan/"><img src="https://avatars.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/HelioStrike"><img src="https://avatars.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/fsal"><img src="https://avatars.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/clennan"><img src="https://avatars.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gmatt"><img src="https://avatars.githubusercontent.com/u/6741625?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/SulemanBhatti"><img src="https://avatars.githubusercontent.com/u/55692967?v=4" class="avatar-user" width="18px;"/></a> <a href="https://rumbarum.github.io/"><img src="https://avatars.githubusercontent.com/u/48576227?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/franquil"><img src="https://avatars.githubusercontent.com/u/3143067?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/rudranshsharma123"><img src="https://avatars.githubusercontent.com/u/67827010?v=4" class="avatar-user" width="18px;"/></a> <a href="https://dwyer.co.za/"><img src="https://avatars.githubusercontent.com/u/2641205?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/alaeddine-13"><img src="https://avatars.githubusercontent.com/u/15269265?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.imxiqi.com/"><img src="https://avatars.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/averkij"><img src="https://avatars.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="18px;"/></a> <a href="https://helaoutar.me/"><img src="https://avatars.githubusercontent.com/u/12495892?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/seraco"><img src="https://avatars.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu1415926"><img src="https://avatars.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://imgbot.net/"><img src="https://avatars.githubusercontent.com/u/31427850?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/NouiliKh"><img src="https://avatars.githubusercontent.com/u/22430520?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://ee.linkedin.com/company/forstod"><img src="https://avatars.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mkhilai"><img src="https://avatars.githubusercontent.com/u/6876258?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/julianpetrich"><img src="https://avatars.githubusercontent.com/u/37179344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/BastinJafari"><img src="https://avatars.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/kkkellyjiang"><img src="https://avatars.githubusercontent.com/u/84776567?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PietroAnsidei"><img src="https://avatars.githubusercontent.com/u/31099206?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Gikiman"><img src="https://avatars.githubusercontent.com/u/50768559?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rjgallego"><img src="https://avatars.githubusercontent.com/u/59635994?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/numb3r3"><img src="https://avatars.githubusercontent.com/u/35718120?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/akanz1"><img src="https://avatars.githubusercontent.com/u/51492342?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/ddelange"><img src="https://avatars.githubusercontent.com/u/14880945?v=4" class="avatar-user" width="18px;"/></a>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

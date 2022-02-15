<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina logo: Jina is a cloud-native neural search framework" width="200px"></a>
</p>

<p align="center">
<b>Cloud-Native Neural Search<sup><a href="https://docs.jina.ai/get-started/neural-search/">?</a></sup> Framework for <i>Any</i> Kind of Data</b>
</p>


<p align=center>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img src="https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg" alt="codecov"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-2.2k%2B-blueviolet?logo=slack&amp;logoColor=white"></a>
</p>

<!-- start jina-description -->

Jina is a neural search framework that empowers anyone to build SOTA and scalable neural search applications in minutes.

🥤 **Serve** - level up your local neural search application as an API service via HTTP, WebSockets or gRPC.

🐙 **Orchestrate** - break down your complicated neural search application to a pipeline of Executors. Compose and share pipelines with the help of pre-built Executors [on the Hub](https://hub.jina.ai).

🚀 **Scale** - scale your neural search applications to meet your availability and throughput requirements. All of Jina's microservices can be scaled independently as needed.

☁️ **Cloud Native** - built and designed to work and scale in the cloud. It offers easy integration with [Docker compose](https://docs.jina.ai/how-to/docker-compose/) and [Kubernetes](https://docs.jina.ai/how-to/kubernetes/).

Beside Jina, Jina AI offers a neural search ecosystem composed of [DocArray](https://docarray.jina.ai), [Hub](https://hub.jina.ai) and [Finetuner](https://finetuner.jina.ai). They are nicely integrated with Jina.

<!-- end jina-description -->

## Install 
```bash
pip install -U jina
```

More install options including Conda, Docker, and Windows [can be found here](https://docs.jina.ai/get-started/install/). 

If you are upgrading from Jina 2:
```bash
pip uninstall jina && pip install -U jina
```

## [Documentation](https://docs.jina.ai)

## Get Started

### Basic Concepts

> 💡 We recommend familiarizing yourself beforehand with [DocArray](https://docarray.jina.ai).

Document, Executor and Flow are three fundamental concepts in Jina.

- [**Document**](https://docarray.jina.ai/) is a data structure contains multi-modal data.
- [**Executor**](https://docs.jina.ai/fundamentals/executor/) is a self-contained component and performs a single task on Documents.
- [**Flow**](https://docs.jina.ai/fundamentals/flow/) ties Executors together into a processing pipeline, provides scalability and facilitates deployments in the cloud.

Leveraging these three concepts, let's build a simple image search with the [Totally Looks Like](https://sites.google.com/view/totally-looks-like-dataset) dataset. This is a microservice version of the [DocArray example](https://github.com/jina-ai/docarray#a-complete-workflow-of-visual-search). 

### Create `Executor` for embedding and storing images

<sup>
Preliminaries: <a href="https://sites.google.com/view/totally-looks-like-dataset">download dataset</a>, <a href="https://pytorch.org/get-started/locally/">install PyTorch & Torchvision</a>
</sup>

We first build an Executor generating embeddings with PyTorch and ResNet50:

```python
from jina import Document, DocumentArray, Executor, requests


class ImageEmbeddingExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        import torchvision

        self.model = torchvision.models.resnet50(pretrained=True)

    @requests
    def embedding(self, docs: DocumentArray, **kwargs):
        docs.apply(self.preproc)  # preprocess images
        docs.embed(self.model, device="cuda")  # embed via GPU to speed up

    def preproc(self, d: Document):
        return (
            d.load_uri_to_image_tensor()  # load
            .set_image_tensor_shape((200, 200))  # resize all to 200x200
            .set_image_tensor_normalization()  # normalize color
            .set_image_tensor_channel_axis(-1, 0)
        )  # switch color axis for the PyTorch model later

```

We need to build the second Executor for storing and retrieving images:

```python
class IndexExecutor(Executor):

    _docs = DocumentArray()

    @requests(on="/index")  # set the function to handle the `/index` endpoint
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)
        docs.clear()  # save bandwidth as it is not needed

    @requests(on="/search")  # set the function to handle the `/search` endpoint
    def search(self, docs: DocumentArray, **kwargs):
        docs.match(self._docs, limit=9)  # limit to returning top 9 matches
        docs[...].embeddings = None  # save bandwidth as it is not needed
        docs[...].blobs = None  # save bandwidth as it is not needed
```


### Orchestrate Executors in a Flow

Building a Flow to wire up the Executors, we can index some images and start searching by sending requests to the Flow APIs. 

> Note that we only index the 100 images now for demonstration purpose:

```python
from jina import Client, Flow

if __name__ == "__main__":
    f = Flow(port_expose=12345).add(uses=ImageEmbeddingExecutor).add(uses=IndexExecutor)
    with f:
        left_da = DocumentArray.from_files("left/*.jpg")
        client = Client(port=12345)
        client.post("/index", left_da[:100])  # index only 100 images
        right_da = DocumentArray.from_files("right/*.jpg")[:1]
        right_da.plot_image_sprites(output="query.png")  # save the query image
        response = client.post("/search", right_da)
        (
            response[0]
            .docs[0]
            .matches.apply(
                lambda d: d.set_image_tensor_channel_axis(
                    0, -1
                ).set_image_tensor_inv_normalization()
            )
            .plot_image_sprites(output="matches.png")
        )  # save the matched images
```

<p align="center">
<img alt="Shell outputs running Flow" src="https://github.com/jina-ai/jina/blob/docs3_0-review-readme-3/.github/images/readme-orchestrate-executors.png" title="running Flow" width="60%"/>
</p>


The images with the same id are expected to be matched. The pretrained ResNet50 indeed find some similar images.
You will find the query image at `query.png` and the top 9 matches at `matches.png`. 
This is everything: You just level up your neural search application as an API service! 🎉

<p align="center">
<a href="https://docs.jina.ai"><img src="https://github.com/jina-ai/jina/blob/docs3_0-review-readme-3/.github/images/readme-totally-look-like.png?raw=true" alt="Visualizing Top 9 Matches" width="60%"></a>
</p>


If you want to expose your application with a REST API so that you can send HTTP requests, 
just set the protocol of the Flow to `http`:

```python
...
if __name__ == "__main__":
    f = (
        Flow(protocol="http", port_expose=12345)
        .add(uses=ImageEmbeddingExecutor)
        .add(uses=IndexExecutor)
    )
    ...
    with f:
        ...
        f.block()

```

Now you can use cURL to send search requests:
```bash
curl -X POST http://127.0.0.1:12345/search -H 'Content-type: application/json' -d '{"data":[{"uri": "<data_set_path>/right/00000.jpg"}]}' > curl_response
```

### Use Docker Compose or Kubernetes

If we want to further upgade your Flow with Docker Compose or Kubernetes, we will first need to containerize the Executors. 
The easiest way to do that is by using [Jina Hub](https://hub.jina.ai).

Move each of the two Executors to a separate folder with one Python file in each:
   - `ImageEmbeddingExecutor` -> 📁 `embed_img/exec.py`
   - `IndexExecutor` -> 📁 `match_img/exec.py`
   
Create a `requirements.txt` in `embed_img` and add `torchvision` as a requirement.

```shell
.
├── embed_img
│     ├── exec.py  # copy-paste codes of ImageEmbeddingExecutor
│     └── requirements.txt  # add the requirement `torchvision`
└── match_img
      └── exec.py  # copy-paste codes of IndexExecutor
```

Push all Executors to [Jina Hub](https://hub.jina.ai). (**Important**: Write down the string you get for the usage. It looks like this `jinahub://1ylut0gf`)
```bash
jina hub push embed_img  # publish at jinahub+docker://1ylut0gf  
jina hub push match_img  # publish at jinahub+docker://258lzh3c 
```

You will get two Hub Executors that can be used for any container.

<p align="center">
<img alt="Shell outputs publishing Executors" src="https://github.com/jina-ai/jina/blob/docs3_0-review-readme-3/.github/images/readme-publish-executors.png" title="publish executors" width="60%"/>
</p>

#### Deploy Flow via Docker Compose

A Flow can generate a Docker Compose configuration file so that you can easily start a Flow via `docker-compose up`.

Replace the `uses` arguments in the Flow with the values you have got from Jina Hub from previous steps. This will run the Flow with containerized Executors.

Generate the docker compose configuration from the Flow using one line of Python code. 

```python
f = (
    Flow(protocol="http", port_expose=12345)
    .add(uses="jinahub+docker://1ylut0gf")
    .add(uses="jinahub+docker://258lzh3c")
)
f.to_docker_compose_yaml()  # By default, stored at `docker-compose.yml`

```

```shell
Flow@62548[I]:Docker compose file has been created under docker-compose.yml. You can use it by running `docker-compose up -f docker-compose.yml`
```
   
Now you can start your neural search application with docker compose.

```shell
docker-compose up
```

<p align="center">
<img alt="Shell outputs running docker-compose" src="https://github.com/jina-ai/jina/blob/docs3_0-review-readme-3/.github/images/readme-docker-compose.png" title="outputs of docker-compose"  width="60%"/>
</p>

#### Deploy Flow via Kubernetes

You can easily deploy a Flow with containerized Executors to a Kubernetes cluster as well.

Create a Kubernetes cluster and get credentials (example in GCP, [more K8s providers here](https://docs.jina.ai/advanced/experimental/kubernetes/#preliminaries)):
```bash
gcloud container clusters create test --machine-type e2-highmem-2  --num-nodes 1 --zone europe-west3-a
gcloud container clusters get-credentials test --zone europe-west3-a --project jina-showcase
```

Create a namespace `flow-k8s-namespace` for demonstration purpose ,
```bash
kubectl create namespace flow-k8s-namespace
```

Generate the kubernetes configuration files using one line of code:
```python
f.to_k8s_yaml('./k8s_config', k8s_namespace='flow-k8s-namespace')
```

```shell
k8s_config
├── executor0
│     ├── executor0-head.yml
│     └── executor0.yml
├── executor1
│     ├── executor1-head.yml
│     └── executor1.yml
└── gateway
      └── gateway.yml
```

Use `kubectl` to deploy your neural search application: 

```shell
kubectl apply -R -f ./k8s_config
```

<p align="center">
<img alt="Shell outputs running k8s" src="https://github.com/jina-ai/jina/blob/docs3_0-review-readme-3/.github/images/readme-k8s.png" title="kubernetes outputs" width="60%"/>
</p>

Run port forwarding so that you can send requests to our Kubernetes application from local CLI : 

```shell
kubectl port-forward svc/gateway -n flow-k8s-namespace 12345:12345
```

Now we have the Flow up running in Kubernetes and we can use the `Client` or cURL to send requests. 

> Note that we are running everything in the cloud and make sure the image URIs are accessible from the Kubernetes cluster.


## Run Quick Demo

- [👗 Fashion image search](https://docs.jina.ai/get-started/hello-world/fashion/): `jina hello fashion`
- [🤖 QA chatbot](https://docs.jina.ai/get-started/hello-world/covid-19-chatbot/): `pip install "jina[demo]" && jina hello chatbot`
- [📰 Multimodal search](https://docs.jina.ai/get-started/hello-world/multimodal/): `pip install "jina[demo]" && jina hello multimodal`
- 🍴 Fork the source of a demo to your folder: `jina hello fork fashion ../my-proj/`
- Create a new Jina project: `jina new hello-jina`

<!-- start support-pitch -->

## Support

- Join our [Slack community](https://slack.jina.ai) to chat to our engineers about your use cases, questions, and
  support queries.
- Join our [Engineering All Hands](https://youtube.com/playlist?list=PL3UBBWOUVhFYRUa_gpYYKBqEAkO4sxmne) meet-up to
  discuss your use case and learn Jina's new features.
    - **When?** The second Tuesday of every month
    - **Where?**
      Zoom ([see our public calendar](https://calendar.google.com/calendar/embed?src=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&ctz=Europe%2FBerlin)/[.ical](https://calendar.google.com/calendar/ical/c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com/public/basic.ics)/[Meetup
      group](https://www.meetup.com/jina-community-meetup/))
      and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

Jina is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE).
[We are actively hiring](https://jobs.jina.ai) AI engineers, solution engineers to build the next neural search
ecosystem in open source.

<!-- end support-pitch -->

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to
your active involvement.

- [Release cycles and development stages](RELEASE.md)
- [Contributing guidelines](CONTRIBUTING.md)
- [Code of conduct](https://github.com/jina-ai/jina/blob/master/.github/CODE_OF_CONDUCT.md)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-204-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="18px;"/></a> <a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="18px;"/></a> <a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="18px;"/></a> <a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="18px;"/></a> <a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="18px;"/></a> <a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="18px;"/></a> <a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="18px;"/></a> <a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rjgallego"><img src="https://avatars.githubusercontent.com/u/59635994?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/sarvesh4396"><img src="https://avatars.githubusercontent.com/u/68162479?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/numb3r3"><img src="https://avatars.githubusercontent.com/u/35718120?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/SirsikarAkshay"><img src="https://avatars.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/Arrrlex"><img src="https://avatars.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/atibaup"><img src="https://avatars.githubusercontent.com/u/1799897?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/winstonww"><img src="https://avatars.githubusercontent.com/u/13983591?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Yongxuanzhang"><img src="https://avatars.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/m4rtinkoenig"><img src="https://avatars.githubusercontent.com/u/90192168?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.mia-altieri.dev/"><img src="https://avatars.githubusercontent.com/u/32723809?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/garimavs"><img src="https://avatars.githubusercontent.com/u/77723358?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/seraco"><img src="https://avatars.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/makram93"><img src="https://avatars.githubusercontent.com/u/6537525?v=4" class="avatar-user" width="18px;"/></a> <a href="https://jakobkruse.com/"><img src="https://avatars.githubusercontent.com/u/42516008?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://geopjr.dev/"><img src="https://avatars.githubusercontent.com/u/18014039?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/guenthermi"><img src="https://avatars.githubusercontent.com/u/6599259?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/sauravgarg540"><img src="https://avatars.githubusercontent.com/u/17601899?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/vivek2301"><img src="https://avatars.githubusercontent.com/u/64314477?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/yk"><img src="https://avatars.githubusercontent.com/u/858040?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/shakurshams"><img src="https://avatars.githubusercontent.com/u/67507873?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/samsja"><img src="https://avatars.githubusercontent.com/u/55492238?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Nishil07"><img src="https://avatars.githubusercontent.com/u/63183230?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ddelange"><img src="https://avatars.githubusercontent.com/u/14880945?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/robertjrodger"><img src="https://avatars.githubusercontent.com/u/15660082?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://www.linkedin.com/in/umairkarel/"><img src="https://avatars.githubusercontent.com/u/76861978?v=4" class="avatar-user" width="18px;"/></a> <a href="https://prasakis.com/"><img src="https://avatars.githubusercontent.com/u/10392953?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/azayz"><img src="https://avatars.githubusercontent.com/u/40893766?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/kilianyp"><img src="https://avatars.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/innerNULL"><img src="https://avatars.githubusercontent.com/u/10429190?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/akanz1"><img src="https://avatars.githubusercontent.com/u/51492342?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/anshulwadhawan"><img src="https://avatars.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/averkij"><img src="https://avatars.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kelton8Z"><img src="https://avatars.githubusercontent.com/u/22567795?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/pswu11"><img src="https://avatars.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/nikos-nalmpantis-60650b187/"><img src="https://avatars.githubusercontent.com/u/67504154?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/davidli-oneflick"><img src="https://avatars.githubusercontent.com/u/62926164?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadejsv"><img src="https://avatars.githubusercontent.com/u/11489772?v=4" class="avatar-user" width="18px;"/></a> <a href="https://cristianmtr.github.io/resume/"><img src="https://avatars.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/CatStark"><img src="https://avatars.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jakubzitny"><img src="https://avatars.githubusercontent.com/u/3315662?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/lucia-loher/"><img src="https://avatars.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/xinbin-huang/"><img src="https://avatars.githubusercontent.com/u/27927454?v=4" class="avatar-user" width="18px;"/></a> <a href="https://raghavprabhakar66.github.io/"><img src="https://avatars.githubusercontent.com/u/52318784?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/Hippopotamus0308"><img src="https://avatars.githubusercontent.com/u/50010436?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.efho.de/"><img src="https://avatars.githubusercontent.com/u/6096895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://yanlong.wang/"><img src="https://avatars.githubusercontent.com/u/565869?v=4" class="avatar-user" width="18px;"/></a> <a href="https://fb.com/saurabh.nemade"><img src="https://avatars.githubusercontent.com/u/17445338?v=4" class="avatar-user" width="18px;"/></a> <a href="https://prabhupad26.github.io/"><img src="https://avatars.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rudranshsharma123"><img src="https://avatars.githubusercontent.com/u/67827010?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/alec-trievel-8b869399/"><img src="https://avatars.githubusercontent.com/u/14189257?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gmastrapas"><img src="https://avatars.githubusercontent.com/u/32414777?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pgiank28"><img src="https://avatars.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/strawberrypie"><img src="https://avatars.githubusercontent.com/u/29224443?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/kaushikb11"><img src="https://avatars.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Gikiman"><img src="https://avatars.githubusercontent.com/u/50768559?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/umbertogriffo"><img src="https://avatars.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/carlosbaezruiz/"><img src="https://avatars.githubusercontent.com/u/1107703?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/xiongma"><img src="https://avatars.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PabloRN"><img src="https://avatars.githubusercontent.com/u/727564?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bsmth"><img src="https://avatars.githubusercontent.com/u/43580235?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/davidbp"><img src="https://avatars.githubusercontent.com/u/4223580?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/FionnD"><img src="https://avatars.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="18px;"/></a> <a href="https://maateen.me/"><img src="https://avatars.githubusercontent.com/u/11742254?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/Shubhamsaboo"><img src="https://avatars.githubusercontent.com/u/31396011?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bio-howard"><img src="https://avatars.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/yuanbit"><img src="https://avatars.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pdaryamane"><img src="https://avatars.githubusercontent.com/u/11886076?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bhavsarpratik"><img src="https://avatars.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sridatta.ml/"><img src="https://avatars.githubusercontent.com/u/17333185?v=4" class="avatar-user" width="18px;"/></a> <a href="http://hargup.in/"><img src="https://avatars.githubusercontent.com/u/2477788?v=4" class="avatar-user" width="18px;"/></a> <a href="https://ee.linkedin.com/company/forstod"><img src="https://avatars.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/deepampatel"><img src="https://avatars.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/BastinJafari"><img src="https://avatars.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/samjoy"><img src="https://avatars.githubusercontent.com/u/3750744?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/serge-m"><img src="https://avatars.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="18px;"/></a> <a href="https://imgbot.net/"><img src="https://avatars.githubusercontent.com/u/31427850?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/fsal"><img src="https://avatars.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/sephiartlist"><img src="https://avatars.githubusercontent.com/u/84024706?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/franquil"><img src="https://avatars.githubusercontent.com/u/3143067?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gmatt"><img src="https://avatars.githubusercontent.com/u/6741625?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/prasanth94"><img src="https://avatars.githubusercontent.com/u/4848556?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jancijen"><img src="https://avatars.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/wanderer163"><img src="https://avatars.githubusercontent.com/u/93438190?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/alaeddine-13"><img src="https://avatars.githubusercontent.com/u/15269265?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JohannesMessner"><img src="https://avatars.githubusercontent.com/u/44071807?v=4" class="avatar-user" width="18px;"/></a> <a href="http://fayeah.github.io/"><img src="https://avatars.githubusercontent.com/u/29644978?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/smy0428"><img src="https://avatars.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Immich"><img src="https://avatars.githubusercontent.com/u/9353470?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/properGrammar"><img src="https://avatars.githubusercontent.com/u/20957896?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/RenrakuRunrat"><img src="https://avatars.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rameshwara"><img src="https://avatars.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ThePfarrer"><img src="https://avatars.githubusercontent.com/u/7157861?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/uvipen"><img src="https://avatars.githubusercontent.com/u/47221207?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://www.linkedin.com/in/akurniawan25/"><img src="https://avatars.githubusercontent.com/u/4723643?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/AnudeepGunukula"><img src="https://avatars.githubusercontent.com/u/55506841?v=4" class="avatar-user" width="18px;"/></a> <a href="https://jina.ai/"><img src="https://avatars.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/qwel-exe"><img src="https://avatars.githubusercontent.com/u/72848513?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/harry-stark"><img src="https://avatars.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bsherifi"><img src="https://avatars.githubusercontent.com/u/32338617?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JamesTang-616"><img src="https://avatars.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Showtim3"><img src="https://avatars.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.milchior.fr/"><img src="https://avatars.githubusercontent.com/u/357361?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/HelioStrike"><img src="https://avatars.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/Roshanjossey"><img src="https://avatars.githubusercontent.com/u/8488446?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/DARREN-ZHANG"><img src="https://avatars.githubusercontent.com/u/8371825?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/educatorsRlearners"><img src="https://avatars.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gauthamsuresh09"><img src="https://avatars.githubusercontent.com/u/55235118?v=4" class="avatar-user" width="18px;"/></a> <a href="http://semantic-release.org/"><img src="https://avatars.githubusercontent.com/u/32174276?v=4" class="avatar-user" width="18px;"/></a> <a href="https://gitcommit.show/"><img src="https://avatars.githubusercontent.com/u/56937085?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sebastianlettner.info/"><img src="https://avatars.githubusercontent.com/u/51201318?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jyothishkjames"><img src="https://avatars.githubusercontent.com/u/937528?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mohamed--abdel-maksoud"><img src="https://avatars.githubusercontent.com/u/1863880?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/10zinten/"><img src="https://avatars.githubusercontent.com/u/16164304?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/hongchhe"><img src="https://avatars.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mezig351"><img src="https://avatars.githubusercontent.com/u/10896185?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadej-redstone"><img src="https://avatars.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/clennan"><img src="https://avatars.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/cpooley"><img src="https://avatars.githubusercontent.com/u/17229557?v=4" class="avatar-user" width="18px;"/></a> <a href="http://freesearch.pe.kr/"><img src="https://avatars.githubusercontent.com/u/957840?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mapleeit"><img src="https://avatars.githubusercontent.com/u/4194287?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/doomdabo"><img src="https://avatars.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mkhilai"><img src="https://avatars.githubusercontent.com/u/6876258?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/janandreschweiger"><img src="https://avatars.githubusercontent.com/u/44372046?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/ManudattaG"><img src="https://avatars.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gvondulong"><img src="https://avatars.githubusercontent.com/u/54177084?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ApurvaMisra"><img src="https://avatars.githubusercontent.com/u/22544948?v=4" class="avatar-user" width="18px;"/></a> <a href="http://gaocegege.com/Blog"><img src="https://avatars.githubusercontent.com/u/5100735?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/fernandakawasaki"><img src="https://avatars.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="18px;"/></a> <a href="https://nech.pl/"><img src="https://avatars.githubusercontent.com/u/1821404?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/alasdairtran"><img src="https://avatars.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/aakashjhawar"><img src="https://avatars.githubusercontent.com/u/22843890?v=4" class="avatar-user" width="18px;"/></a> <a href="https://helaoutar.me/"><img src="https://avatars.githubusercontent.com/u/12495892?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/Gracegrx"><img src="https://avatars.githubusercontent.com/u/23142113?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/NouiliKh"><img src="https://avatars.githubusercontent.com/u/22430520?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ggdupont"><img src="https://avatars.githubusercontent.com/u/5583410?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="18px;"/></a> <a href="https://lenincodes.co/socials"><img src="https://avatars.githubusercontent.com/u/61219881?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jacobowitz"><img src="https://avatars.githubusercontent.com/u/6544965?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PietroAnsidei"><img src="https://avatars.githubusercontent.com/u/31099206?v=4" class="avatar-user" width="18px;"/></a> <a href="https://shivaylamba.me/"><img src="https://avatars.githubusercontent.com/u/19529592?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/julianpetrich"><img src="https://avatars.githubusercontent.com/u/37179344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.carecloud.com/"><img src="https://avatars.githubusercontent.com/u/55692967?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://dwyer.co.za/"><img src="https://avatars.githubusercontent.com/u/2641205?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/CallmeMehdi"><img src="https://avatars.githubusercontent.com/u/47258917?v=4" class="avatar-user" width="18px;"/></a> <a href="https://rumbarum.github.io/"><img src="https://avatars.githubusercontent.com/u/48576227?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/dalekatwork"><img src="https://avatars.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Bharat123rox"><img src="https://avatars.githubusercontent.com/u/13381361?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu1415926"><img src="https://avatars.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/LukeekuL"><img src="https://avatars.githubusercontent.com/u/24293913?v=4" class="avatar-user" width="18px;"/></a> <a href="http://bit.ly/3qKM0uO"><img src="https://avatars.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/kkkellyjiang"><img src="https://avatars.githubusercontent.com/u/84776567?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/aga11313"><img src="https://avatars.githubusercontent.com/u/23415764?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://blog.lsgrep.com/"><img src="https://avatars.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/KING-SID"><img src="https://avatars.githubusercontent.com/u/14876698?v=4" class="avatar-user" width="18px;"/></a> <a href="http://willperkins.com/"><img src="https://avatars.githubusercontent.com/u/576702?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.imxiqi.com/"><img src="https://avatars.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="18px;"/></a>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

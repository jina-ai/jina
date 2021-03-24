<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina banner" width="400px">
</p>
<p align="center">
<h2 align="center">Deep Learning Search Framework for Any Kind of Data</h2>
</p>
<p align=center>
<!--<a href="https://github.com/jina-ai/jina/actions?query=workflow%3ACI"><img src="https://github.com/jina-ai/jina/workflows/CI/badge.svg" alt="CI"></a>-->
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://pepy.tech/project/jina"><img src="https://pepy.tech/badge/jina/month"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-500%2B-blueviolet"></a>
</p>

Jina is a search framework for building <strong>cross-/multi-media search systems</strong> on the cloud, powered by best-in-class AI models.

<table>
  <tr>
    <td>
      <a href="https://docs.jina.ai/">
        <img src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world.gif?raw=true" />
      </a>
    </td>
    <td>
<a href="https://docs.jina.ai/">
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-chatbot.gif?raw=true" />
</a>
    </td>
    <td>
<a href="https://youtu.be/B_nH8GCmBfc">
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-multimodal.gif?raw=true" />
</a>
    </td>
  </tr>
  <tr>
    <th>
      <a href="http://demo.jina.ai/#image-search">Image search</a>
    </th>
    <th>
      <a href="http://demo.jina.ai/#chatbot">Q+A Chatbot</a>
    </th>
    <th>
      <a href="http://demo.jina.ai/#cross-media">Cross-Media search</a>
    </td>
  </tr>
</table>

With Jina you can search through any kind of data with machine learning models pre-trained and released by Facebook, Google, Spotify, and more. With the modular framework you can find the right tool for the right job -- whether that's crafting, encoding, classifying, indexing, or querying data. Alternatively, assemble them all into one [Flow](https://101.jina.ai/#Flow) for a unified end-to-end experience. 

Configuration is stored in YAML files, away from your actual code. So tweaking model parameters or other settings is a breeze, especially with our [YAML completion feature for PyCharm and VS Code](https://youtu.be/qOD-6mihUzQ).

## Why Jina?

⏱️ **Save time** - *The* design pattern of neural search systems, from zero to a production-ready system in minutes.

🍱 **Own your stack** - Keep an end-to-end stack ownership of your solution, avoid the integration pitfalls with fragmented, multi-vendor, generic legacy tools.

🌌 **Search anything** - Large-scale indexing and querying of unstructured data: video, image, long/short text, music, source code, etc.

🧠 **First-Class AI Models** - First-class support for [state-of-the-art AI models](https://docs.jina.ai/chapters/all_exec.html), easily usable and extendable with a Pythonic interface.

🌩️ **Scale up to the Cloud** - Decentralized architecture from day one. Scalable & cloud-native by design: enjoy containerizing, distributing, sharding, async, REST/gRPC/WebSocket.

❤️  **Made with Love** - Never compromise on quality, actively maintained by a [passionate full-time, venture-backed team](https://jina.ai).

## Installation

See our [installation guide](https://docs.jina.ai/chapters/core/setup/) for installing Jina Daemon/extras/pre-releases, or installing on Windows.

#### With `pip`

```sh
pip install -U jina
```

#### With Docker

```sh
docker run jinaai/jina:latest
```

## Get Started

### The Basics

- What is neural search, and how is it different to symbolic search?
- Jina 101: Learn Jina's key components
- Jina 102: Learn how Jina's components fit together
- My First Jina App: Build your first simple app

### Run a Demo

- [Fashion MNIST image search](http://demo.jina.ai/#image-search): blah blah blah
- [Q+A chatbot](http://demo.jina.ai/#image-search): blah blah blah
- [Cross media search](http://demo.jina.ai/#image-search): blah blah blah

### Examples ([View all](https://github.com/jina-ai/examples))

Example code to build your own projects

<table>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/wikipedia-sentences">NLP Semantic Wikipedia Search with Transformers and DistilBERT</a></h4>
      Brand new to neural search? See a simple text-search example to understand how Jina works
    </td>
  </tr>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/wikipedia-sentences-incremental">Add Incremental Indexing to Wikipedia Search</a></h4>
      Index more effectively by adding incremental indexing to your Wikipedia search
    </td>
  </tr>
  <tr>
    <td>
      <h1>📄</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Search Lyrics with Transformers and PyTorch</a></h4>
      Get a better understanding of chunks by searching a lyrics database. Now with shiny front-end!
    </td>
  </tr>
  <tr>
    <td>
      <h1>🖼️</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Google's Big Transfer Model in (Poké-)Production</a></h4>
      Use SOTA visual representation for searching Pokémon!
    </td>
  </tr>
  <tr>
    <td>
      <h1>🎧</h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/audio-search">Search YouTube audio data with Vggish</a></h4>
      A demo of neural search for audio data based Vggish model.
    </td>
  </tr>
  <tr>
    <td>
      <h1>🎞️ </h1>
    </td>
    <td>
      <h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Search Tumblr GIFs with KerasEncoder</a></h4>
      Use prefetching and sharding to improve the performance of your index and query Flow when searching animated GIFs.
    </td>
  </tr>
</table>

Please check our [examples repo](https://github.com/jina-ai/examples) for advanced and community-submitted examples.

Want to read more? Check our Founder [Han Xiao's blog](https://hanxiao.io) and [our official blog](https://jina.ai/blog).

## How Does it Work?

Every Jina app uses [Flows]() to index or query your data:

**`app.py`**

```python
from jina.flow import Flow

f = Flow.load_config('flows/index.yml') # Load Flow config from YAML file

with f:
    f.index_lines("my_data.txt") # Index each line of the text file as a single document
```

A Flow lays out all of the steps to process and index your data, and can be written in [YAML](https://docs.jina.ai/chapters/yaml/) or directly in [Python](https://docs.jina.ai/chapters/flow/). A very simple Flow looks like:

**`flows/index.yml`**

```yaml
!Flow
version: '1'
pods:
  - name: encoder
    uses: pods/encode.yml
  - name: indexer
    uses: pods/index.yml
```

Each step (encoding, indexing) is performed by a [Pod](), with its settings once again defined in YAML:

**`pods/encode.yml`**

```yaml
!TransformerTorchEncoder
with:
  pretrained_model_name_or_path: distilbert-base-cased # name of your pretrained model
  ... # other (optional) encoder settings
```

To start indexing your data, simply run:

```sh
python app.py index
```

Or run `python app.py query` to start querying your data via a [REST](https://docs.jina.ai/chapters/restapi/index.html) or gRPC gateway.

For a simple app example check [Wikipedia sentence search]() or see [My First Jina App]() to build your own.

## Documentation

Apart from the learning resources above, We highly recommended you go through our [**documentation**](https://docs.jina.ai) to master Jina.

Our docs are built on every push, merge, and release of Jina's master branch. Documentation for older versions is archived [here](https://github.com/jina-ai/docs/releases).

Are you a "Doc"-star? Join us! We welcome all kinds of improvements on the documentation.

## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to your active involvement.

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

### Contributors ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-133-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tadej-redstone"><img src="https://avatars.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/NouiliKh"><img src="https://avatars.githubusercontent.com/u/22430520?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://prasakis.com/"><img src="https://avatars.githubusercontent.com/u/10392953?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/fsal"><img src="https://avatars.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://www.efho.de/"><img src="https://avatars.githubusercontent.com/u/6096895?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/deepampatel"><img src="https://avatars.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/xinbinhuang"><img src="https://avatars.githubusercontent.com/u/27927454?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/robertjrodger"><img src="https://avatars.githubusercontent.com/u/15660082?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/lucia-loher/"><img src="https://avatars.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://bit.ly/3qKM0uO"><img src="https://avatars.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/harry-stark"><img src="https://avatars.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/seraco"><img src="https://avatars.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jacobowitz"><img src="https://avatars.githubusercontent.com/u/6544965?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/aga11313"><img src="https://avatars.githubusercontent.com/u/23415764?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://jina.ai/"><img src="https://avatars.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/tadejsv"><img src="https://avatars.githubusercontent.com/u/11489772?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/FionnD"><img src="https://avatars.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/PabloRN"><img src="https://avatars.githubusercontent.com/u/727564?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/prabhupad-pradhan/"><img src="https://avatars.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Immich"><img src="https://avatars.githubusercontent.com/u/9353470?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/pgiank28"><img src="https://avatars.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/yuanb/"><img src="https://avatars.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fayeah"><img src="https://avatars.githubusercontent.com/u/29644978?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/HelioStrike"><img src="https://avatars.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ManudattaG"><img src="https://avatars.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/mezig351"><img src="https://avatars.githubusercontent.com/u/10896185?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/pswu11"><img src="https://avatars.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/julianpetrich"><img src="https://avatars.githubusercontent.com/u/37179344?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/BastinJafari"><img src="https://avatars.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/samjoy"><img src="https://avatars.githubusercontent.com/u/3750744?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/akurniawan25/"><img src="https://avatars.githubusercontent.com/u/4723643?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/atibaup"><img src="https://avatars.githubusercontent.com/u/1799897?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/cpooley"><img src="https://avatars.githubusercontent.com/u/17229557?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/SirsikarAkshay"><img src="https://avatars.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://shivaylamba.netlify.app/"><img src="https://avatars.githubusercontent.com/u/19529592?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/doomdabo"><img src="https://avatars.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/umbertogriffo"><img src="https://avatars.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Roshanjossey"><img src="https://avatars.githubusercontent.com/u/8488446?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/anshulwadhawan"><img src="https://avatars.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.imxiqi.com/"><img src="https://avatars.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bsherifi"><img src="https://avatars.githubusercontent.com/u/32338617?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/clennan"><img src="https://avatars.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://sebastianlettner.info/"><img src="https://avatars.githubusercontent.com/u/51201318?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/friedsiberian"><img src="https://avatars.githubusercontent.com/u/79760314?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/carlosbaezruiz/"><img src="https://avatars.githubusercontent.com/u/1107703?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/LukeekuL"><img src="https://avatars.githubusercontent.com/u/24293913?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/davidbp"><img src="https://avatars.githubusercontent.com/u/4223580?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://kilsenp.github.io/"><img src="https://avatars.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Gracegrx"><img src="https://avatars.githubusercontent.com/u/23142113?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/davidli-oneflick"><img src="https://avatars.githubusercontent.com/u/62926164?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="http://willperkins.com/"><img src="https://avatars.githubusercontent.com/u/576702?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ThePfarrer"><img src="https://avatars.githubusercontent.com/u/7157861?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/averkij"><img src="https://avatars.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/fernandakawasaki"><img src="https://avatars.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/serge-m"><img src="https://avatars.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/rjgallego"><img src="https://avatars.githubusercontent.com/u/59635994?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ApurvaMisra"><img src="https://avatars.githubusercontent.com/u/22544948?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://github.com/bio-howard"><img src="https://avatars.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/yk"><img src="https://avatars.githubusercontent.com/u/858040?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/jyothishkjames"><img src="https://avatars.githubusercontent.com/u/937528?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/uvipen"><img src="https://avatars.githubusercontent.com/u/47221207?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/ddelange"><img src="https://avatars.githubusercontent.com/u/14880945?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="http://hargup.in/"><img src="https://avatars.githubusercontent.com/u/2477788?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/smy0428"><img src="https://avatars.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://cristianmtr.github.io/resume/"><img src="https://avatars.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/janandreschweiger"><img src="https://avatars.githubusercontent.com/u/44372046?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/Yongxuanzhang"><img src="https://avatars.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="32px;"/></a></kbd>
<kbd><a href="https://blog.lsgrep.com/"><img src="https://avatars.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/PietroAnsidei"><img src="https://avatars.githubusercontent.com/u/31099206?v=4" class="avatar-user" width="32px;"/></a></kbd> <kbd><a href="https://github.com/hongchhe"><img src="https://avatars.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="32px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Community

- [Code of conduct](https://github.com/jina-ai/jina/blob/master/.github/CODE_OF_CONDUCT.md) - play nicely with the Jina community
- [Slack workspace](https://slack.jina.ai) - join #general on our Slack to meet the team and ask questions
- [YouTube channel](https://youtube.com/c/jina-ai) - subscribe to the latest video tutorials, release demos, webinars and presentations.
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - get to know Jina AI as a company and find job opportunities
- [![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - follow and interact with us using hashtag `#JinaSearch`
- [Company](https://jina.ai) - know more about our company and how we are fully committed to open-source.

## Open Governance

<a href="https://www.youtube.com/c/jina-ai">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/eah-god.png?raw=true " />
</a>

As part of our open governance model, we host Jina's [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) in public. This Zoom meeting recurs monthly on the second Tuesday of each month, at 14:00-15:30 (CET). Everyone can join in via the following calendar invite.

- [Add to Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Download .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

The meeting will also be live-streamed and later published to our [YouTube channel](https://youtube.com/c/jina-ai).

## Join Us

Jina is an open-source project. [We are hiring](https://jobs.jina.ai) full-stack developers, evangelists, and PMs to build the next neural search ecosystem in open source.


## License

Copyright (c) 2020-2021 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [See LICENSE for the full license text.](LICENSE)

<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/logo-only.gif?raw=true" alt="Jina banner" width="200px">
</p>

<p align="center">
<b>Cloud-Native Neural Search Framework for <i>Any</i> Kind of Data</b>
</p>


<p align=center>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8 3.9" title="Jina supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jina?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://pepy.tech/project/jina"><img src="https://pepy.tech/badge/jina/month"></a>
<a href="https://codecov.io/gh/jina-ai/jina"><img src="https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg" alt="codecov"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-500%2B-blueviolet"></a>
</p>

<details>
<summary>👋 Click here to see quick demo!</summary>

<table>
  <tr>
    <td width="30%">
      <a href="./.github/pages/hello-world.md#-fashion-image-search">
        <img src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world.gif?raw=true" />
      </a>
    </td>
    <td width="30%">
<a href="./.github/pages/hello-world.md#-covid-19-chatbot">
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-chatbot.gif?raw=true" />
</a>
    </td>
    <td width="30%">
<a href="https://youtu.be/B_nH8GCmBfc">
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-multimodal.gif?raw=true" />
</a>
    </td>
  </tr>
  <tr>
    <th>
      <a href="./.github/pages/hello-world.md#-fashion-image-search">Image search</a>
    </th>
    <th>
      <a href="./.github/pages/hello-world.md#-covid-19-chatbot">QA chatbot</a>
    </th>
    <th>
      <a href="./.github/pages/hello-world.md#-multimodal-document-search">Multi-media search</a>
    </th>
  </tr>
</table>

</details>

Jina is geared towards building search systems for any kind of data, including [text](https://github.com/jina-ai/examples/tree/master/wikipedia-sentences), [images](https://github.com/jina-ai/examples/tree/master/pokedex-with-bit), [audio](https://github.com/jina-ai/examples/tree/master/audio-search), [video](https://github.com/jina-ai/examples/tree/master/tumblr-gif-search) and [many more](https://github.com/jina-ai/examples). With the modular design & multi-layer abstraction, you can leverage the efficient patterns to build the system by parts, or chaining them into a [Flow](https://101.jina.ai/#Flow) for an end-to-end experience.


🌌 **Search anything** - Large-scale indexing and querying of unstructured data: video, image, long/short text, music, source code, etc.

⏱️ **Save time** - *The* design pattern of neural search systems, from zero to a production-ready system in minutes.

🍱 **Own your stack** - Keep an end-to-end stack ownership of your solution, avoid the integration pitfalls with fragmented, multi-vendor, generic legacy tools.

🧠 **First-class AI models** - First-class support for [state-of-the-art AI models](https://docs.jina.ai/chapters/all_exec.html), easily usable and extendable with a Pythonic interface.

🌩️ **Fast & cloud-ready** - Decentralized architecture from day one. Scalable & cloud-native by design: enjoy containerizing, distributing, sharding, async, REST/gRPC/WebSocket.


## Installation

```sh
pip install -U jina
```

#### via Docker

```sh
docker run jinaai/jina:latest
```

<details>
<summary>📦 More installation options</summary>

| <br><sub><sup>x86/64,arm/v6,v7,[v8 (Apple M1)](https://github.com/jina-ai/jina/issues/1781)</sup></sub> | On Linux/macOS & Python 3.7/3.8/[3.9](https://github.com/jina-ai/jina/issues/1801) | Docker Users|
| --- | --- | --- |
| Standard | `pip install -U jina` | `docker run jinaai/jina:latest` |
| <sub><a href="https://api.jina.ai/daemon/">Daemon</a></sub> | <sub>`pip install -U "jina[daemon]"`</sub> | <sub>`docker run --network=host jinaai/jina:latest-daemon`</sub> |
| <sub>With Extras</sub> | <sub>`pip install -U "jina[devel]"`</sub> | <sub>`docker run jinaai/jina:latest-devel`</sub> |
| <sub>Dev/Pre-Release</sub> | <sub>`pip install --pre jina`</sub> | <sub>`docker run jinaai/jina:master`</sub> |

Version identifiers [are explained here](https://github.com/jina-ai/jina/blob/master/RELEASE.md). To install Jina with extra dependencies [please refer to the docs](https://docs.jina.ai/chapters/install/via-pip.html). Jina can run on [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

</details>

<details>
<summary>💡 YAML Completion in PyCharm & VSCode</summary>

Developing Jina app often means writing YAML configs. We provide a [JSON Schema](https://json-schema.org/) for your IDE to enable code completion, syntax validation, members listing and displaying help text. Here is a [video tutorial](https://youtu.be/qOD-6mihUzQ) to walk you through the setup.

<table>
  <tr>
    <td>
<a href="https://www.youtube.com/watch?v=qOD-6mihUzQ&ab_channel=JinaAI"><img src="https://github.com/jina-ai/jina/blob/master/.github/images/pycharm-schema.gif?raw=true" /></a>
    </td>
    <td>

**PyCharm**

1. Click menu `Preferences` -> `JSON Schema mappings`;
2. Add a new schema, in the `Schema File or URL` write `https://api.jina.ai/schemas/latest.json`; select `JSON Schema Version 7`;
3. Add a file path pattern and link it to `*.jaml` and `*.jina.yml`.

</td>
</tr>
<tr>
    <td>
<a href="https://www.youtube.com/watch?v=qOD-6mihUzQ&ab_channel=JinaAI"><img src="https://github.com/jina-ai/jina/blob/master/.github/images/vscode-schema.gif?raw=true" /></a>
    </td>
    <td>

**VSCode**

1. Install the extension: `YAML Language Support by Red Hat`;
2. In IDE-level `settings.json` add:

```json
"yaml.schemas": {
    "https://api.jina.ai/schemas/latest.json": ["/*.jina.yml", "/*.jaml"],
}
```

</td>
</tr>
</table>
</details>

## Get Started


### Cookbook

[Bits, pieces and examples of Jina code](./.github/pages/snippets.md)

### Run Quick Demo

- [👗 Fashion image search](./.github/pages/hello-world.md#-fashion-image-search): `jina hello fashion`
- [🤖 QA chatbot](./.github/pages/hello-world.md#-covid-19-chatbot): `pip install "jina[chatbot]" && jina hello chatbot`
- [📰 Multimedia search](./.github/pages/hello-world.md#-multimodal-document-search): `pip install "jina[multimodal]" && jina hello multimodal`

### The Basics

- [What is neural search, and how is it different to symbolic search?](https://jina.ai/2020/07/06/What-is-Neural-Search-and-Why-Should-I-Care.html)
- [Jina 101: Learn Jina's key components](https://docs.jina.ai/chapters/101/)
- [Jina 102: Learn how Jina's components fit together](https://docs.jina.ai/chapters/102/)
- [My First Jina App: Build your first simple app](https://docs.jina.ai/chapters/my_first_jina_app/)


### Video Tutorials

<table>
  <tr>
    <td width="33%">
    <a href="https://youtu.be/zvXkQkqd2I8">
      <img src="https://github.com/jina-ai/jina/blob/master/.github/images/basic-concept.png?raw=true"/>
    </a>
    </td>
    <td width="33%">
    <a href="https://youtu.be/qOD-6mihUzQ">
      <img src="https://github.com/jina-ai/jina/blob/master/.github/images/speedup.png?raw=true"/>
    </a>
    </td>
    <td width="33%">
    <a href="https://youtu.be/B_nH8GCmBfc">
      <img src="https://github.com/jina-ai/jina/blob/master/.github/images/multimodal-search.png?raw=true"/>
    </a>
    </td>
  </tr>
</table>


### Examples ([View all](https://github.com/jina-ai/examples))
 
#### [📄 NLP Semantic Wikipedia Search with Transformers and DistilBERT](https://github.com/jina-ai/examples/tree/master/wikipedia-sentences)
&nbsp;&nbsp;&nbsp;&nbsp;Brand new to neural search? See a simple text-search example to understand how Jina works 

#### [📄 Add Incremental Indexing to Wikipedia Search](https://github.com/jina-ai/examples/tree/master/wikipedia-sentences-incremental)
&nbsp;&nbsp;&nbsp;&nbsp;Index more effectively by adding incremental indexing to your Wikipedia search 

#### [📄 Search Lyrics with Transformers and PyTorch](https://github.com/jina-ai/examples/tree/master/multires-lyrics-search)
&nbsp;&nbsp;&nbsp;&nbsp;Get a better understanding of chunks by searching a lyrics database. Now with shiny front-end! 

#### [🖼️ Google's Big Transfer Model in (Poké-)Production](https://github.com/jina-ai/examples/tree/master/pokedex-with-bit)
&nbsp;&nbsp;&nbsp;&nbsp;Use SOTA visual representation for searching Pokémon!

#### [🎧 Search YouTube audio data with Vggish](https://github.com/jina-ai/examples/tree/master/audio-search)
&nbsp;&nbsp;&nbsp;&nbsp;A demo of neural search for audio data based Vggish model. 

#### [🎞️ Search Tumblr GIFs with KerasEncoder](https://github.com/jina-ai/examples/tree/master/tumblr-gif-search)
&nbsp;&nbsp;&nbsp;&nbsp;Use prefetching and sharding to improve the performance of your index and query Flow when searching animated GIFs.

Check our [examples repo](https://github.com/jina-ai/examples) for advanced and community-submitted examples.

## Documentation & Support

- Docs: https://docs.jina.ai
- Join our [Slack community](https://slack.jina.ai) to chat to our engineers about your use cases, questions, and support queries.
- Join our Engineering All Hands meet-up to discuss your use case and learn Jina's new features.
    - **When?** The second Tuesday of every month
    - **Where?** Zoom ([calendar link](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)/[.ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)) and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai).


## Contributing

We welcome all kinds of contributions from the open-source community, individuals and partners. We owe our success to your active involvement.

- [Contributing guidelines](CONTRIBUTING.md)
- [Code of conduct](https://github.com/jina-ai/jina/blob/master/.github/CODE_OF_CONDUCT.md) - play nicely with the Jina community
- [Good first issues](https://github.com/jina-ai/jina/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
- [Release cycles and development stages](RELEASE.md)
- [Upcoming features](https://portal.productboard.com/jinaai/) - what's being planned, what we're thinking about.



<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-141-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="18px;"/></a> <a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="18px;"/></a> <a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="18px;"/></a> <a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="18px;"/></a> <a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="18px;"/></a> <a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="18px;"/></a> <a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="18px;"/></a> <a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/serge-m"><img src="https://avatars.githubusercontent.com/u/4344566?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/akurniawan25/"><img src="https://avatars.githubusercontent.com/u/4723643?v=4" class="avatar-user" width="18px;"/></a> <a href="https://shivaylamba.netlify.app/"><img src="https://avatars.githubusercontent.com/u/19529592?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pdaryamane"><img src="https://avatars.githubusercontent.com/u/11886076?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/ThePfarrer"><img src="https://avatars.githubusercontent.com/u/7157861?v=4" class="avatar-user" width="18px;"/></a> <a href="https://jina.ai/"><img src="https://avatars.githubusercontent.com/u/11627845?v=4" class="avatar-user" width="18px;"/></a> <a href="https://prasakis.com/"><img src="https://avatars.githubusercontent.com/u/10392953?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/harry-stark"><img src="https://avatars.githubusercontent.com/u/43717480?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/franquil"><img src="https://avatars.githubusercontent.com/u/3143067?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/umbertogriffo"><img src="https://avatars.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/hongchhe"><img src="https://avatars.githubusercontent.com/u/25891193?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/BastinJafari"><img src="https://avatars.githubusercontent.com/u/25417797?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PietroAnsidei"><img src="https://avatars.githubusercontent.com/u/31099206?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rjgallego"><img src="https://avatars.githubusercontent.com/u/59635994?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/jancijen"><img src="https://avatars.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/xinbin-huang/"><img src="https://avatars.githubusercontent.com/u/27927454?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/seraco"><img src="https://avatars.githubusercontent.com/u/25517036?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jacobowitz"><img src="https://avatars.githubusercontent.com/u/6544965?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/janandreschweiger"><img src="https://avatars.githubusercontent.com/u/44372046?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/SirsikarAkshay"><img src="https://avatars.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/robertjrodger"><img src="https://avatars.githubusercontent.com/u/15660082?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Arrrlex"><img src="https://avatars.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/julianpetrich"><img src="https://avatars.githubusercontent.com/u/37179344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/MiaAltieri"><img src="https://avatars.githubusercontent.com/u/32723809?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/bhavsarpratik"><img src="https://avatars.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/strawberrypie"><img src="https://avatars.githubusercontent.com/u/29224443?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/doomdabo"><img src="https://avatars.githubusercontent.com/u/72394295?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadejsv"><img src="https://avatars.githubusercontent.com/u/11489772?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sebastianlettner.info/"><img src="https://avatars.githubusercontent.com/u/51201318?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/FionnD"><img src="https://avatars.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="18px;"/></a> <a href="http://willperkins.com/"><img src="https://avatars.githubusercontent.com/u/576702?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/dalekatwork"><img src="https://avatars.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/mezig351"><img src="https://avatars.githubusercontent.com/u/10896185?v=4" class="avatar-user" width="18px;"/></a> <a href="http://bit.ly/3qKM0uO"><img src="https://avatars.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/alasdairtran"><img src="https://avatars.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/anshulwadhawan"><img src="https://avatars.githubusercontent.com/u/25061477?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/atibaup"><img src="https://avatars.githubusercontent.com/u/1799897?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/prabhupad-pradhan/"><img src="https://avatars.githubusercontent.com/u/11462012?v=4" class="avatar-user" width="18px;"/></a> <a href="https://kilsenp.github.io/"><img src="https://avatars.githubusercontent.com/u/5173119?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/tadej-redstone"><img src="https://avatars.githubusercontent.com/u/69796623?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/deepampatel"><img src="https://avatars.githubusercontent.com/u/19245659?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/aga11313"><img src="https://avatars.githubusercontent.com/u/23415764?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/yk"><img src="https://avatars.githubusercontent.com/u/858040?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/LukeekuL"><img src="https://avatars.githubusercontent.com/u/24293913?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/NouiliKh"><img src="https://avatars.githubusercontent.com/u/22430520?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pswu11"><img src="https://avatars.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/rameshwara"><img src="https://avatars.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/PabloRN"><img src="https://avatars.githubusercontent.com/u/727564?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/jyothishkjames"><img src="https://avatars.githubusercontent.com/u/937528?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Kelton8Z"><img src="https://avatars.githubusercontent.com/u/22567795?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/uvipen"><img src="https://avatars.githubusercontent.com/u/47221207?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/averkij"><img src="https://avatars.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/nicholas-cwh/"><img src="https://avatars.githubusercontent.com/u/25291155?v=4" class="avatar-user" width="18px;"/></a> <a href="https://dwyer.co.za/"><img src="https://avatars.githubusercontent.com/u/2641205?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://www.linkedin.com/in/yuanb/"><img src="https://avatars.githubusercontent.com/u/12972261?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Yongxuanzhang"><img src="https://avatars.githubusercontent.com/u/44033547?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bio-howard"><img src="https://avatars.githubusercontent.com/u/74507907?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/bsherifi"><img src="https://avatars.githubusercontent.com/u/32338617?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/cpooley"><img src="https://avatars.githubusercontent.com/u/17229557?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ddelange"><img src="https://avatars.githubusercontent.com/u/14880945?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/saurabhnemade"><img src="https://avatars.githubusercontent.com/u/17445338?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/RenrakuRunrat"><img src="https://avatars.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/davidbp"><img src="https://avatars.githubusercontent.com/u/4223580?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/carlosbaezruiz/"><img src="https://avatars.githubusercontent.com/u/1107703?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/mohamed--abdel-maksoud"><img src="https://avatars.githubusercontent.com/u/1863880?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/davidli-oneflick"><img src="https://avatars.githubusercontent.com/u/62926164?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/amrit3701/"><img src="https://avatars.githubusercontent.com/u/10414959?v=4" class="avatar-user" width="18px;"/></a> <a href="https://blog.lsgrep.com/"><img src="https://avatars.githubusercontent.com/u/3893940?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/pgiank28"><img src="https://avatars.githubusercontent.com/u/17511966?v=4" class="avatar-user" width="18px;"/></a> <a href="http://fayeah.github.io/"><img src="https://avatars.githubusercontent.com/u/29644978?v=4" class="avatar-user" width="18px;"/></a> <a href="https://cristianmtr.github.io/resume/"><img src="https://avatars.githubusercontent.com/u/8330330?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Showtim3"><img src="https://avatars.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="18px;"/></a> <a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/smy0428"><img src="https://avatars.githubusercontent.com/u/61920576?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/JamesTang-616"><img src="https://avatars.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="18px;"/></a> <a href="http://www.efho.de/"><img src="https://avatars.githubusercontent.com/u/6096895?v=4" class="avatar-user" width="18px;"/></a> <a href="https://sreerag-ibtl.github.io/"><img src="https://avatars.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="18px;"/></a> <a href="http://hargup.in/"><img src="https://avatars.githubusercontent.com/u/2477788?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/clennan"><img src="https://avatars.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.linkedin.com/in/lucia-loher/"><img src="https://avatars.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/YueLiu1415926"><img src="https://avatars.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/ApurvaMisra"><img src="https://avatars.githubusercontent.com/u/22544948?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Roshanjossey"><img src="https://avatars.githubusercontent.com/u/8488446?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/ManudattaG"><img src="https://avatars.githubusercontent.com/u/8463344?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Immich"><img src="https://avatars.githubusercontent.com/u/9353470?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/kaushikb11"><img src="https://avatars.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="18px;"/></a> <a href="https://www.imxiqi.com/"><img src="https://avatars.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/Gracegrx"><img src="https://avatars.githubusercontent.com/u/23142113?v=4" class="avatar-user" width="18px;"/></a> <a href="https://stackoverflow.com/users/7513718/el-aoutar-hamza"><img src="https://avatars.githubusercontent.com/u/12495892?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/samjoy"><img src="https://avatars.githubusercontent.com/u/3750744?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/fsal"><img src="https://avatars.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="18px;"/></a> <a href="https://github.com/fernandakawasaki"><img src="https://avatars.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="18px;"/></a>
<a href="https://github.com/HelioStrike"><img src="https://avatars.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="18px;"/></a>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->


## Join Us

Jina is backed by [Jina AI](https://jina.ai). [We are hiring](https://jobs.jina.ai) full-stack developers, evangelists, and PMs to build the next neural search ecosystem in open source.

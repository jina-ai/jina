<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/1500x667new.gif?raw=true" alt="Jina banner" width="100%">
</p>

<p align="center">

[![Jina](https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true  "Jina is licensed under Apache-2.0")](#license)
[![Python 3.7 3.8](https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true  "Jina supports Python 3.7 and above")](https://pypi.org/project/jina/)
[![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/)
[![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina is multi-arch ready, can run on different architectures")](https://hub.docker.com/r/jinaai/jina/tags)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jinaai/jina?color=%23099cec&label=Docker%20Image&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)
[![API Schema](https://github.com/jina-ai/jina/workflows/API%20Schema/badge.svg)](https://api.jina.ai/)
[![codecov](https://codecov.io/gh/jina-ai/jina/branch/master/graph/badge.svg)](https://codecov.io/gh/jina-ai/jina)

</p>

<p align="center">
  <a href="https://github.com/jina-ai/jina">English</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.pt_br.md">Português (BR)</a>
</p>


<p align="center">
  <a href="https://jina.ai">Website</a> •
  <a href="https://docs.jina.ai">Docs</a> •
  <a href="https://learn.jina.ai">Examples</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://dashboard.jina.ai">Dashboard (beta)</a> •
  <a href="https://github.com/jina-ai/jinabox.js/">Jinabox (beta)</a> •
  <a href="http://www.twitter.com/JinaAI_">Twitter</a> •
  <a href="https://jobs.jina.ai">We are Hiring</a>
</p>

Jina é um framework de pesquisa baseada em IA, que permite que desenvolvedores criem sistemas de busca **cross/multi-modals** (como texto, imagens, video, áudio) na nuvem. Jina é mantida a logo prazo por [um grupo movido pela aventura em tempo integral](https://jina.ai).

⏱️ **Economia de tempo** - Inicie um sistema impulsionado por IA em poucos minutos.

🧠 **Modelos de IA de primeira classe** - Jina é um novo padrão de design para sistemas neurais de pesquisa com apoio especial para [modelos de IA de state-of-the-art](https://docs.jina.ai/chapters/all_exec.html).

🌌 **Busca universal** - Indexação de larga escala e consulta de qualquer tipo em várias plataformas. Vídeo, imagem, texto curto/longo, código-fonte, e mais.

🚀 **Production Ready** - Features nativas de nuvem que funcionam "out-of-the-box" (fora da caixa), por ex. conteinerização, microsserviço, distribuição, escalabilidade (scaling), sharding, async IO, REST, gRPC.

🧩 **Conecte e use** - Com [Jina Hub](https://github.com/jina-ai/jina-hub), é fácil expandir Jina com simples scripts em Python ou com Imagens Docker otimizadas para seu campo de pesquisa.

## Sumário

<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/install.png?raw=true " />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Instalação](#instala%C3%A7%C3%A3o)
- [Jina "Olá, mundo!" 👋🌍](#jina-ol%C3%A1-mundo-)
- [Tutoriais](#tutoriais)
- [Documentação](#documenta%C3%A7%C3%A3o)
- [Contribuindo](#contribuindo)
- [Comunidade](#comunidade)
- [Governança Aberta](#governan%C3%A7a-aberta)
- [Junte-se a nós](#junte-se-a-n%C3%B3s)
- [Licença](#licen%C3%A7a)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Instalação

### Com PyPi

No sistemas operacionais Linux/MacOS com Python >= 3.7:

```bash
pip install jina
```

Para instalar Jina em dependências adicionais ou no Raspberry Pi, [favor checar a documentação](https://docs.jina.ai).

### Em um Container Docker

Nós oferecemos uma Imagem Docker universal com suporte para diversos tipos de arquitetura (incluindo x64, x86, arm-64/v7/v6). É só rodar:

```bash
docker run jinaai/jina --help
```

## Jina "Olá, mundo!" 👋🌍

Paara começar, você pode tentar nosso "Hello, World" (que significa "Olá, mundo") - uma simples demonstração de busca neural de imagem para [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). Nenhuma outra dependência é necessária. É só rodar:

```bash
jina hello-world
```

...ou, mais facilmente, para usuários de Docker, **sem instalação necessária**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # substituir "open" por "xdg-open" no Linux
```

<details>
<summary>Clique aqui para ver a saída do console</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>

A Imagem Docker baixa o treinamento e o dataset de teste do Fashion-MNIST e diz para Jina indexar 60.000 imagens dos dados de treinamento. Em seguida, a Imagem Docker seleciona amostras aleatórias de imagens do teste, as define como queries e pede para Jina extrair os resultados relevantes. Todo esse processo leva em torno de 1 minuto, e eventualmente abre uma página web com resultados, que se parecem com esse:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

A implementação por trás disso é simples:

<table>
<tr>
<td> Python API </td>
<td> ou use <a href="https://github.com/jina-ai/jina/blob/master/jina/resources/helloworld.flow.index.yml">YAML spec</a></td>
<td> ou use <a href="https://github.com/jina-ai/dashboard">Dashboard</a></td>
</tr>
<tr>
<td>


```python
from jina.flow import Flow

f = (Flow()
        .add(uses='encoder.yml', parallel=2)
        .add(uses='indexer.yml', shards=2,
             separated_workspace=True))

with f:
    f.index(fashion_mnist, batch_size=1024)
```

</td>
<td>

```yaml
!Flow
pods:
  encode:
    uses: encoder.yml
    parallel: 2
  index:
    uses: indexer.yml
    shards: 2
    separated_workspace: true
```

</td>
<td>

![Flow in Dashboard](https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-flow.png?raw=true)

</td>
</tr>
</table>

<details>
<summary><strong>Explore sharding, conteinerização, concatenação de embeddings, e mais</strong></summary>

#### Adicionando Paralelismo e Sharding

```python
from jina.flow import Flow

f = (Flow().add(uses='encoder.yml', parallel=2)
           .add(uses='indexer.yml', shards=2, separated_workspace=True))
```

#### [Distribuindo Flow](https://docs.jina.ai/chapters/remote/index.html)

```python
from jina.flow import Flow

f = Flow().add(uses='encoder.yml', host='192.168.0.99')
```

#### [Usando um Container Docker](https://docs.jina.ai/chapters/hub/index.html)

```python
from jina.flow import Flow

f = (Flow().add(uses='jinahub/cnn-encode:0.1')
           .add(uses='jinahub/faiss-index:0.2', host='192.168.0.99'))
```

#### Concatenando embeddings

```python
from jina.flow import Flow

f = (Flow().add(name='eb1', uses='BiTImageEncoder')
           .add(name='eb2', uses='KerasImageEncoder', needs='gateway')
           .needs(['eb1', 'eb2'], uses='_concat'))
```

#### [Permitindo Network Query](https://docs.jina.ai/chapters/restapi/index.html)

```python
from jina.flow import Flow

f = Flow(port_expose=45678, rest_api=True)

with f:
    f.block()
```

Ficou interessado(a)? Explore outras opções:

```bash
jina hello-world --help
```
</details>

### Crie seu primeiro projeto com Jina

```bash
pip install jina[devel]
jina hub new --type app
```

Você pode facilmente criar um projeto com Jina a partir de templates, basta um comando no terminal. Este comando acima cria um ponto de entrada (entrypoint) de Python, configurações YAML e um Dockerfile. Você pode começar a partir dali.


## Tutoriais

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/101/img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: A primeira coisa para se aprender sobre Jina</a></h3>
&nbsp;&nbsp;<a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">English</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.pt.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ar.md">عربية</a>
    </td>

  </tr>
</table>

<table>
<tr>
<th width="10%">Nível</th>
<th width="90%">Tutoriais</th>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">Construir um sistema de busca semântica com PLN (NLP)</a></h4>
Procure scripts de South Park e pratique com Flows e Pods
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">Meu primeiro App com Jina</a></h4>
Use cookiecutter para iniciar um app com Jina
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">Fashion Search com Query Language (Linguagem de consulta)</a></h4>
Torne o Hello-World mais interessante com uma Query Language
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Use Chunk para procurar letras de músicas</a></h4>
Divida documentos para procurar em um nível detalhado
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/cross-modal-search">Misture e combine imagens e legendas</a></h4>
Procure cross modal para conseguir imagens a partir de suas legendas e vice-e-versa
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Aumente a intensidade da busca semântica de vídeo</a></h4>
Melhore a performance usando prefetching e sharding
</td>
</tr>

<!-- <tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/x-as-service">De BERT-as-Service até X-as-Service</a></h4>
Extraia elementos de dados vetoriais (vector data) usando qualquer representação de deep learning
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Big Transfer Model do Google em (Poké-)Produção</a></h4>
Procure Pokémon com a representação visual de state-of-the-art</td>
</tr>
 -->
</table>

## Documentação

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

A melhor maneira de aprender Jina de forma aprofundada é lendo nossa documentação. A documentação é construída em cima de cada push, merge, e release na branch master.

#### O básico

- [Use Flow API para compor o seu Workflow de busca](https://docs.jina.ai/chapters/flow/index.html)
- [Funções de Entrada e Saída em Jina](https://docs.jina.ai/chapters/io/index.html)
- [Use Dashboard para conseguir Insight do Workflow de Jina](https://github.com/jina-ai/dashboard)
- [Distribua seu Workflow remotamente](https://docs.jina.ai/chapters/remote/index.html)
- [Rode Jina Pods via Conteiner Docker](https://docs.jina.ai/chapters/hub/index.html)

#### Referência

- [Argumentos de interface da linha de comando](https://docs.jina.ai/chapters/cli/index.html)
- [Interface Python API](https://docs.jina.ai/api/jina.html)
- [YAML sintaxe para Executor, Driver e Flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Protobuf schema](https://docs.jina.ai/chapters/proto/index.html)
- [Variáveis de ambiente](https://docs.jina.ai/chapters/envs.html)
- ... [e mais](https://docs.jina.ai/index.html)

Você é um(a) "Doc"-star? Junte-se a nós! Todo tipo de ajuda na documentação é bem-vindo.

[Documentação para versões antigas está arquivada aqui](https://github.com/jina-ai/docs/releases).

## Contribuindo

Todo tipo de contribuição da comunidade open-source é bem-vindo, individuais e parceiros. Nós devemos nosso sucesso à sua participação ativa.

- [Orientações para contribuição](CONTRIBUTING.md)
- [Ciclos de Release e estágios de desenvolvimento](RELEASE.md)

### Contribuidores ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-66-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars1.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars1.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars0.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars1.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars1.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/lusloher"><img src="https://avatars2.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars2.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars2.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/pswu11"><img src="https://avatars2.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars1.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://stackoverflow.com/story/umbertogriffo"><img src="https://avatars2.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars3.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://www.imxiqi.com/"><img src="https://avatars2.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars3.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars1.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars3.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars0.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="50px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Comunidade

- [Slack workspace](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - junte-se ao #general no nosso Slack para conhecer o time e fazer perguntas
- [Canal no YouTube](https://youtube.com/c/jina-ai) - inscreva-se para receber nossos tutoriais mais recentes, demos de release, webinários e apresentações
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - conheça Jina AI como uma empresa e encontre oportunidades de emprego
- [![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - siga e interaja conosco usando a hashtag `#JinaSearch`
- [Empresa](https://jina.ai) - aprenda mais sobre nossa empresa e como somos totalmente comprometidos com open-source.

## Governança Aberta

[Marcos/milestones GitHub](https://github.com/jina-ai/jina/milestones) planeje o caminho para futuras melhoras de Jina.

Como parte do nosso modelo de governança aberta, nós hosteamos [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) de Jina publicamente. Essa reunião no Zoom ocorre mensalmente na segunda terça-feira de cada mês, às 14:00-15:30 (CET). Qualquer um pode se juntar por meio do convite de calendário a seguir.

- [Adicionar ao Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Download .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

Será feita uma live-stream da reunião, que depois será publicada em nosso [Canal do YouTube](https://youtube.com/c/jina-ai).

## Junte-se a nós

Jina é um projeto open-source. [Estamos contratando](https://jobs.jina.ai) desenvolvedores full-stack, evangelists, e PMs para construir o próximo ecossistema de busca neural em open source.


## Licença

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [See LICENSE for the full license text.](LICENSE)

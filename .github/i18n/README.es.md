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
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.kr.md">한국어</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">український</a>
</p>


<p align="center">
  <a href="https://jina.ai">Sitio Web</a> •
  <a href="https://docs.jina.ai">Documentos</a> •
  <a href="https://learn.jina.ai">Ejemplos</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://dashboard.jina.ai">Dashboard (beta)</a> •
  <a href="https://github.com/jina-ai/jinabox.js/">Jinabox (beta)</a> •
  <a href="http://www.twitter.com/JinaAI_">Twitter</a> •
  <a href="https://jobs.jina.ai">Estamos contratando</a>
</p>

Jina es un framework de búsqueda basado en IA que permite a los desarrolladores crear sistemas de búsqueda **cross/multi-modals** (como texto, imágenes, video, audio) en la nube.

⏱️ **Ahorro de tiempo** - Inicie un sistema AI-powered en sólo unos minutos..

🧠 **Modelos IA de primera clase** - *El* patrón de diseño de los sistemas de búsqueda neuronal, con soporte de primera clase para [modelos IA de última generación](https://docs.jina.ai/chapters/all_exec.html).

🌌 **Búsqueda universal** - indexación y consulta a gran escala de cualquier tipo de datos en múltiples plataformas: vídeo, imagen, texto largo/corto, música, código fuente, etc.

☁️ **Cloud Ready** - Arquitectura descentralizada con características propias cloud-natives: contenedorización, microservicio, escalado, sharding, async IO, REST, gRPC.

🧩 **Plug & Play** - Fácilmente ampliable con la interfaz Pythonic.

❤️ **Hecho con amor** - La calidad es lo primero, nunca se compromete, mantenido por un [equipo a tiempo completo, respaldado por la empresa](https://jina.ai).


## Resumen

<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/install.png?raw=true " />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Instalación](#instalaci%C3%B3n)
- [Jina "Hola, mundo!" 👋🌍](#jina-hola-mundo-)
- [Tutoriales](#tutoriales)
- [Documentación](#documentaci%C3%B3n)
- [Contribuyendo](#contribuyendo)
- [Comunidad](#comunidad)
- [Gobernanza abierta](#gobernanza-abierta)
- [Únase](#%C3%BAnase)
- [Licencia](#licencia)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Instalación

### Con PyPi

En sistemas operativos Linux/MacOS con Python >= 3.7:

```bash
pip install jina
```

Para instalar Jina con dependencias adicionales o en Raspberry Pi, [por favor revise la documentación](https://docs.jina.ai).

### En un contenedor Docker

Ofrecemos una imagen Docker universal con soporte para varios tipos de arquitectura (incluyendo x64, x86, arm-64/v7/v6). Simplemente funciona:

```bash
docker run jinaai/jina --help
```

## Jina "Hola, mundo!" 👋🌍

Para empezar, puede probar nuestro "Hola, Mundo" - una simple demostración de búsqueda de imágenes mediante redes neuronales  [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No se necesitan dependencias adicionales, simplemente ejecute:

```bash
jina hello-world
```

...o, más fácilmente, para los usuarios de Docker, **sin necesidad de instalación**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # Reemplaza "open" por "xdg-open" en Linux
```

<details>
<summary>Haga clic aquí para ver la salida en la consola</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>

La imagen de  Docker descarga el conjunto de datos de entrenamiento y pruebas del Fashion-MNIST y le dice a Jina que indexe 60.000 imágenes de los datos de entrenamiento. La imagen de Docker selecciona muestras aleatorias de imágenes de prueba, las define como consultas y le pide a Jina que extraiga los resultados relevantes. Todo este proceso toma alrededor de 1 minuto, y eventualmente abre una página web con resultados, que se ven así:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

La implementación detrás de esto es simple:

<table>
<tr>
<td> Python API </td>
<td> o use <a href="https://github.com/jina-ai/jina/blob/master/jina/resources/helloworld.flow.index.yml">YAML spec</a></td>
<td> o use <a href="https://github.com/jina-ai/dashboard">Dashboard</a></td>
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
<summary><strong>Explore el sharding, la contenedorización, la concatenación de incrustaciones y más</strong></summary>

#### Adicionando Paralelismo y Sharding

```python
from jina.flow import Flow

f = (Flow().add(uses='encoder.yml', parallel=2)
           .add(uses='indexer.yml', shards=2, separated_workspace=True))
```

#### [Distribuyendo Flow](https://docs.jina.ai/chapters/remote/index.html)

```python
from jina.flow import Flow

f = Flow().add(uses='encoder.yml', host='192.168.0.99')
```

#### [Usando un Contenedor de Docker](https://docs.jina.ai/chapters/hub/index.html)

```python
from jina.flow import Flow

f = (Flow().add(uses='jinahub/cnn-encode:0.1')
           .add(uses='jinahub/faiss-index:0.2', host='192.168.0.99'))
```

#### Conectando embeddings

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

¿Está interesado? Explora otras opciones:

```bash
jina hello-world --help
```
</details>

### Cree su primer proyecto con Jina

```bash
pip install jina[devel]
jina hub new --type app
```

Puede crear fácilmente un proyecto con Jina a partir de plantillas, sólo con un comando en la terminal. Este comando de arriba crea un punto de entrada de Python(entrypoint), ajustes de YAML y un Dockerfile. Puedes empezar desde ahí.


## Tutoriales

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/101/img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: Lo primero que debe aprender sobre Jina</a></h3>
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
<th width="10%">Nivel</th>
<th width="90%">Tutoriales</th>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">Construir un sistema de búsqueda semántica con PLN (NLP)</a></h4>
Busque los scripts de South Park y practique con Flows y Pods
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">Mi primera app con Jina</a></h4>
Usa cookiecutter para iniciar una app con Jina
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">Fashion Search con Query Language (lenguaje de consulta)</a></h4>
Hacer que Hello-World sea más interesante con un lenguaje de consulta
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Use Chunk para buscar letras de canciones</a></h4>
Divida los documentos para buscar a nivel detallado
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/cross-modal-search">Mezcle y combine imágenes y subtítulos</a></h4>
Busque el cross modal para obtener imágenes de sus subtítulos y viceversa
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Aumente la intensidad de la búsqueda semántica de video</a></h4>
Mejore el rendimiento utilizando el prefetching y el sharding
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

## Documentación

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

La mejor manera de aprender  Jina en profundidad es leyendo nuestra documentación. La documentación se construye sobre cada actualización y publicación en la rama master.

#### El básico

- [Utilice la API de flujo para componer su Workflow (flujo de trabajo) de búsqueda](https://docs.jina.ai/chapters/flow/index.html)
- [Funciones de entrada y salida en Jina](https://docs.jina.ai/chapters/io/index.html)
- [Registra y monitorea con el Dashboard gráfico de Jina](https://github.com/jina-ai/dashboard)
- [Distribuya su Workflow(flujo de trabajo) de forma remota](https://docs.jina.ai/chapters/remote/index.html)
- [Construye tu Pod en una imagen Docker: Cómo y por qué](https://docs.jina.ai/chapters/hub/index.html)

#### Referencia

- [Argumentos de la interfaz de la línea de comando(CLI)](https://docs.jina.ai/chapters/cli/index.html)
- [interfaz Python API](https://docs.jina.ai/api/jina.html)
- [Sintaxis YAML para Executor, Driver y Flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Protobuf schema](https://docs.jina.ai/chapters/proto/index.html)
- [Las variables de entorno](https://docs.jina.ai/chapters/envs.html)
- ... [y más](https://docs.jina.ai/index.html)

¿Eres una estrella del "Doc"? ¡Únase a nosotros! Toda clase de ayuda con la documentación es bienvenida.

[La documentación de las versiones anteriores está archivada aquí](https://github.com/jina-ai/docs/releases).

## Contribuyendo

Todo tipo de contribuciones de la comunidad de código abierto son bienvenidas, individuos y socios. Debemos nuestro éxito a su participación activa.

- [Pautas para la contribución](CONTRIBUTING.md)
- [Ciclos de publicación y etapas de desarrollo](RELEASE.md)

### Colaboradores ✨

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

## Comunidad

- [Slack workspace](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - Únase al General en nuestro Slack para conocer al equipo y hacer preguntas
- [Canal en YouTube](https://youtube.com/c/jina-ai) - regístrese para nuestros últimos tutoriales, demostraciones de lanzamiento, seminarios web y presentaciones
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - conozca  Jina AI como empresa y encuentre oportunidades de trabajo
- [![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - síganos e interactue con nosotros usando hashtag `#JinaSearch`
- [Empresa](https://jina.ai) - aprenda más sobre nuestra empresa y cómo estamos totalmente comprometidos con el código abierto.

## Gobernanza abierta
[Marcos/milestones GitHub](https://github.com/jina-ai/jina/milestones) planee el camino para las futuras mejoras de Jina.

Como parte de nuestro modelo de gobernanza abierta, alojamos [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) de Jina publicamente. Esta reunión en Zoom tiene lugar mensualmente el segundo martes de cada mes a las 14:00-15:30 (CET). Cualquiera puede unirse mediante la siguiente invitación del calendario.

- [Adicionar al Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Download .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

Se hará una transmisión en vivo de la reunión, que luego se publicará en nuestro [Canal de YouTube](https://youtube.com/c/jina-ai).

## Únase

Jina es un proyecto open-source. [Estamos contratando](https://jobs.jina.ai) desarrolladores full-stack, evangelistas, y PMs para construir el próximo ecosistema de búsqueda neural de código abierto(open-source)

## Licencia

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina está licenciada bajo la Licencia Apache, Version 2.0. [Ver LICENCIA para el texto completo de la licencia.](LICENSE)

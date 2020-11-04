<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/1500x667new.gif?raw=true" alt="Банер Jina" width="100%">
</p>

<p align="center">

[![Jina](https://github.com/jina-ai/jina/blob/master/.github/badges/license-badge.svg?raw=true  "Jina має ліцензію Apache-2.0")](#license)
[![Python 3.7 3.8](https://github.com/jina-ai/jina/blob/master/.github/badges/python-badge.svg?raw=true  "Jina підтримує Python 3.7 та вище")](https://pypi.org/project/jina/)
[![PyPI](https://img.shields.io/pypi/v/jina?color=%23099cec&label=PyPI%20package&logo=pypi&logoColor=white)](https://pypi.org/project/jina/)
[![Docker](https://github.com/jina-ai/jina/blob/master/.github/badges/docker-badge.svg?raw=true  "Jina є мультиархітектурною та може працювати на пристроях з різною архітектурою")](https://hub.docker.com/r/jinaai/jina/tags)
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
  <a href="https://github.com/jina-ai/jina/blob/master/README.zh.md">Português (BR)</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/README.uk.md">Українська</a>
</p>


<p align="center">
  <a href="https://jina.ai">Сайт</a> •
  <a href="https://docs.jina.ai">Документація</a> •
  <a href="https://learn.jina.ai">Зразки</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://dashboard.jina.ai">Dashboard (beta)</a> •
  <a href="https://github.com/jina-ai/jinabox.js/">Jinabox (beta)</a> •
  <a href="http://www.twitter.com/JinaAI_">Twitter</a> •
  <a href="https://jobs.jina.ai">Ми наймаємо</a>

</p>

Jina - це пошукова система на основі ШІ, яка надає розробникам можливість створювати **крос-/мульти-модальні пошукові системи** (напр. текст, зображення, відео, аудіо) у хмарі. Jina має довгострокову підтримку [командою, яка працює full-time та має венчурну підтримку](https://jina.ai).

⏱️ **Економія часу** - Завантажте систему з ШІ лише за кілька хвилин.

🧠 **Взірцеві моделі ШІ** - Jina являє собою новий шаблон проєктування для нейронних пошукових систем з блискучою підтримкою [найсучасніших моделей ШІ](https://docs.jina.ai/chapters/all_exec.html).

🌌 **Універсальний пошук** - Широкомасштабне індексування та запити даних будь-якого типу на багатьох платформах. Відео, зображення, об'ємні/короткі тести, музика, вихідний код, та більше.

🚀 **Готове до використання** - Cloud-native можливості працюють одразу "з коробки", напр. контейнеризація, мікросервіси, розповсюдження, масштабування, sharding, асинхронні IO, REST, gRPC.

🧩 **Підключіть та грайте** - Разом з [Jina Hub](https://github.com/jina-ai/jina-hub), з легкістю розширюйте Jina за допомогою Python-скриптів або образів Docker, оптимізованих для ваших сфер пошуку.

## Зміст

<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/install.png?raw=true " />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Розпочнімо](#%D0%A0%D0%BE%D0%B7%D0%BF%D0%BE%D1%87%D0%BD%D1%96%D0%BC%D0%BE)
- [Jina "Привіт, світе!" 👋🌍](#jina-%D0%9F%D1%80%D0%B8%D0%B2%D1%96%D1%82-%D1%81%D0%B2%D1%96%D1%82%D0%B5-)
- [Туторіали](#%D0%A2%D1%83%D1%82%D0%BE%D1%80%D1%96%D0%B0%D0%BB%D0%B8)
- [Документація](#%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D0%B0%D1%86%D1%96%D1%8F)
- [Допомога проєкту](#%D0%94%D0%BE%D0%BF%D0%BE%D0%BC%D0%BE%D0%B3%D0%B0-%D0%BF%D1%80%D0%BE%D1%94%D0%BA%D1%82%D1%83)
- [Спільнота](#%D0%A1%D0%BF%D1%96%D0%BB%D1%8C%D0%BD%D0%BE%D1%82%D0%B0)
- [Відкрите управління](#%D0%92%D1%96%D0%B4%D0%BA%D1%80%D0%B8%D1%82%D0%B5-%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D1%96%D0%BD%D0%BD%D1%8F)
- [Приєднуйтесь](#%D0%9F%D1%80%D0%B8%D1%94%D0%B4%D0%BD%D1%83%D0%B9%D1%82%D0%B5%D1%81%D1%8C)
- [Ліцензія](#%D0%9B%D1%96%D1%86%D0%B5%D0%BD%D0%B7%D1%96%D1%8F)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Розпочнімо

### З PyPi

На пристроях Linux/MacOS з Python >= 3.7:

```bash
pip install jina
```

Для того, щоб встановити разом з Jina додаткові залежності або щоб встановити на Raspberry Pi, [будь-ласка, зверніть увагу на документацію](https://docs.jina.ai).

### У Docker-контейнері

Ми пропонуємо універсальний образ Docker, який підтримує різноманітні архітектури (Включаючи x64, x86, arm-64/v7/v6). Просто запустіть:

```bash
docker run jinaai/jina --help
```

## Jina "Привіт, світе!" 👋🌍

Як новачок, ви можете спробувати наш "Привіт, світе" - просте демо нейропошуку по зображеннях для [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). Жодних додаткових залежностей, просто запустіть:

```bash
jina hello-world
```

...або для користувачів Docker навіть ще простіше, **не потребуючи встановлення**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # замініть "open" на "xdg-open" на Linux
```

<details>
<summary>Натисніть тут, щоб побачити вивід консолі</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="привіт світе вивід консолі">
</p>

</details>

Образ Docker завантажує навчально-тестовий набір даних Fashion-MNIST та каже Jina проіндексувати 60,000 зображень із навчального набору. Тоді він випадковим чином обирає зображення з тестового набору як запити та просить Jina отримати відповідні результати. Весь процес займає близько 1 хвилини, і в підсумку відкривається вебсторінка на якій відображаються такі результати:

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="банер Jina" width="90%">
</p>

Реалізація цього є досить простою:

<table>
<tr>
<td> Python API </td>
<td> або використовуючи <a href="https://github.com/jina-ai/jina/blob/master/jina/resources/helloworld.flow.index.yml">YAML spec</a></td>
<td> або використовуючи <a href="https://github.com/jina-ai/dashboard">Dashboard</a></td>
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
<summary><strong>Дослідіть sharding, контейнеризацію, об'єднування вкладень, та більше</strong></summary>

#### Додавання паралелізму та Sharding

```python
from jina.flow import Flow

f = (Flow().add(uses='encoder.yml', parallel=2)
           .add(uses='indexer.yml', shards=2, separated_workspace=True))
```

#### [Розподіл потоку](https://docs.jina.ai/chapters/remote/index.html)

```python
from jina.flow import Flow

f = Flow().add(uses='encoder.yml', host='192.168.0.99')
```

#### [Використання Docker-контейнера](https://docs.jina.ai/chapters/hub/index.html)

```python
from jina.flow import Flow

f = (Flow().add(uses='jinahub/cnn-encode:0.1')
           .add(uses='jinahub/faiss-index:0.2', host='192.168.0.99'))
```

#### Об'єднання вкладень

```python
from jina.flow import Flow

f = (Flow().add(name='eb1', uses='BiTImageEncoder')
           .add(name='eb2', uses='KerasImageEncoder', needs='gateway')
           .needs(['eb1', 'eb2'], uses='_concat'))
```

#### [Увімкнення мережевих запитів](https://docs.jina.ai/chapters/restapi/index.html)

```python
from jina.flow import Flow

f = Flow(port_expose=45678, rest_api=True)

with f:
    f.block()
```

Заінтриговані? Зіграйте з різними варіантами:

```bash
jina hello-world --help
```
</details>

### Створіть свій перший Jina-проєкт

```bash
pip install jina[devel]
jina hub new --type app
```

Ви можете легко створити Jina-проєкт із шаблонів використовуючи лише одну команду терміналу. Це створює точку входу Python, конфігурації YAML та файл Docker. Ви можете почати звідти.


## Туторіали

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/101/img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 концепт книги з ілюстраціями, Авторські права Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: Перше, що варто вивчити про Jina</a></h3>
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
<th width="10%">Рівень</th>
<th width="90%">Туторіали</th>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">Створення семантичної пошуковиої системи з обробки природньої мови</a></h4>
Пошук сценаріїв "South Park" та тренування з Flows та Pods
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">Мій перший Jina-застосунок</a></h4>
Використання cookiecutter для покрокової збірки jina-застосунку
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">Витончений пошук з мовою запитів</a></h4>
Приправте Hello-World з мовою запитів
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">Використання Chunk для пошуку текстів пісень</a></h4>
Розділіть документи для пошуку на роздрібненому рівні
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/cross-modal-search">Змішування та поєднання зображень та підписів</a></h4>
Шукайте крос-модально, щоб отримувати зображення із субтитрів та навпаки
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">Масштабування семантичного пошуку по відео</a></h4>
Покращіть продуктивність використовуючи попереднє отримання (prefetching) та sharding
</td>
</tr>

<!-- <tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/x-as-service">From BERT-as-Service to X-as-Service</a></h4>
Extract feature vector data using any deep learning representation
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/pokedex-with-bit">Google's Big Transfer Model in (Poké-)Production</a></h4>
Search Pokemon with state-of-the-art visual representation
</td>
</tr>
 -->
</table>

## Документація

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

Найкращий спосіб поглиблено вивчити Jina - прочитати нашу документацію. Вона написана на основі кожного push, merge, та release головної гілки.

#### Основи

- [Використання Flow API для компонування пошукових процесів](https://docs.jina.ai/chapters/flow/index.html)
- [Функції введення та виведення у Jina](https://docs.jina.ai/chapters/io/index.html)
- [Використання Dashboard, щоб отримання статистики робочих процесів Jina](https://github.com/jina-ai/dashboard)
- [Віддалений розподіл робочих процесів](https://docs.jina.ai/chapters/remote/index.html)
- [Запуск Jina Pods з допомогою Docker-контейнера](https://docs.jina.ai/chapters/hub/index.html)

#### Посилання

- [Аргументи інтерфейсу командного рядка](https://docs.jina.ai/chapters/cli/index.html)
- [Інтерфейс Python API](https://docs.jina.ai/api/jina.html)
- [Синтаксис YAML для Executor, Driver та Flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Схеми Protobuf](https://docs.jina.ai/chapters/proto/index.html)
- [Змінні середовища](https://docs.jina.ai/chapters/envs.html)
- ... [та більше](https://docs.jina.ai/index.html)

Ви "Док"-зірка? Приєднуйтесь! Ми вітаємо будь-які покращення документації.

[Документації для попередніх версій зберігаються тут](https://github.com/jina-ai/docs/releases).

## Допомога проєкту

Ми вітаємо буль-які внески від учасників open-source спільноти, окремих осіб та партнерів. Своїм успіхом ми завдячуємо вашій активній участі.

- [Правила допомоги](CONTRIBUTING.md)
- [Цикли випуску та стадії розробки](RELEASE.md)

### Учасники проєкту ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-71-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/clennan"><img src="https://avatars3.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars1.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fernandakawasaki"><img src="https://avatars2.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars3.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars1.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars1.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/HelioStrike"><img src="https://avatars1.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/averkij"><img src="https://avatars0.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://stackoverflow.com/story/umbertogriffo"><img src="https://avatars2.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars2.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.imxiqi.com/"><img src="https://avatars2.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/pswu11"><img src="https://avatars2.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars1.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars1.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/FionnD"><img src="https://avatars0.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars0.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars2.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars1.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars3.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/lusloher"><img src="https://avatars2.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/jancijen"><img src="https://avatars0.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars3.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="50px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Спільнота

- [Slack workspace](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - долучіться до #general на нашому Slack, щоб зустрітися з командою та задати питання
- [YouTube канал](https://youtube.com/c/jina-ai) - підпишіться заради найновіших відео-туторіалів, демо нових випусків, вебінарів та презентацій.
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - познайомтесь з Jina AI як компанією та знайдіть можливості для працевлаштування
- [![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - слідкуйте та взаємодійте з нами використовуючи хештег `#JinaSearch`
- [Компанія](https://jina.ai) - дізнайтесь більше про нашу компанію та як ми повністю віддані open-source.

## Відкрите управління

[GitHub milestones](https://github.com/jina-ai/jina/milestones) викладають шлях майбутніх вдосконалень Jina.

В рамках нашої відкритої моделі управління, ми ведемо Jina [Engineering All Hands]((https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/)) публічно. Ці Zoom-зустрічі відбуваються щомісячно у другий вівторок кожного місяця, о 14:00-15:30 (CET). Кожен може приєднатися через наступне запрошення календаря.

- [Додати до Google Calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [Завантажити .ics](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

Зустріч також буде транслюватися наживо та пізніше буде опублікована на нашому [YouTube каналі](https://youtube.com/c/jina-ai).

## Приєднуйтесь

Jina - це проєкт з відкритим вихідним кодом. [Ми наймаємо](https://jobs.jina.ai) full-stack розробників, євангелістів та PM-ів для побудови майбутньої екосистеми з нейропошуку з відкритим вихідним кодом.


## Ліцензія

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. [Повний текст ліцензії розміщено у файлі LICENSE.](LICENSE)

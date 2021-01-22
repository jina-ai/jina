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
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.pt_br.md">український</a> •
  <a href="https://github.com/jina-ai/jina/blob/master/.github/i18n/README.es.md">Español</a>
</p>


<p align="center">
  <a href="https://jina.ai">웹사이트</a> •
  <a href="https://docs.jina.ai">문서들</a> •
  <a href="https://learn.jina.ai">예</a> •
  <a href="https://github.com/jina-ai/jina-hub">허브(허브)</a> •
  <a href="https://dashboard.jina.ai">대시보드(메시지)</a> •
  <a href="https://github.com/jina-ai/jinabox.js/">지나복스 (beta)</a> •
  <a href="http://www.twitter.com/JinaAI_">트위터</a> •
  <a href="https://jobs.jina.ai">고용정보.</a>

</p>

지나(Jina)는 AI로 구동되는 검색 프레임워크로 개발자가 클라우드 상에 **크로스/멀티-모달 검색 시스템**(예: 텍스트, 이미지, 비디오, 오디오)을 만들 수 있도록 한다. 지나는 [풀타임, 벤처후원팀]의 지원을 받고 있다.(https://jina.ai).

⏱️ **시간 절약** - 몇 분 안에 AI로 구동되는 시스템을 부트스트랩한다.

🧠 **최상의 AI 모델** - 지나(Jina)는 신경 검색 시스템의 새로운 디자인 패턴으로, [최첨단 AI 모델]을 최상급으로 지원한다.(https://docs.jina.ai/chapters/all_exec.html).

🌌 **광범위한 검색** - 여러 플랫폼에서 모든 종류의 대규모 인덱싱 및 데이터 쿼리를 지원한다: 비디오, 이미지, 긴/짧은 텍스트, 음악, 소스 코드 등

🚀 **클라우드 준비** - 컨테이너화, 마이크로 서비스, 배포, 확장, 샤딩, 비동기 IO, REST, gRPC와 같은 클라우드 네이티브 기능을 사용하는 분산형 아키텍쳐이다.

🧩 **플러그 앤 플레이** - Pythonic 인터페이스로 쉽게 확장할 수 있다.

## Contents

<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/install.png?raw=true " />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [시작](#%EC%B0%A9%EC%88%98%ED%95%98%EB%8B%A4)
- [Jina “Hello, World!” 👋🌍](#jina-%EC%95%88%EB%85%95-%EC%84%B8%EA%B3%84-)
- [튜토리얼](#%EC%9E%90%EC%8A%B5%EC%84%9C)
- [문서화](#%EB%AC%B8%EC%84%9C%ED%99%94)
- [기여](#%EA%B8%B0%EC%97%AC%ED%95%98%EB%8A%94)
- [커뮤니티](#community)
- [오픈 거버넌스](#%EC%98%A4%ED%94%88-%EA%B1%B0%EB%B2%84%EB%84%8C%EC%8A%A4)
- [참여하기](#%EC%B0%B8%EC%97%AC%ED%95%98%EA%B8%B0)
- [라이선스](#%EB%A9%B4%ED%97%88%EC%A6%9D)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## 설치

Python 3.7/3.8이 포함된 Linux/MacOS:

```bash
pip install jina
```

추가적인 의존성을 가진 Jina를 설치하거나, Raspberry Pi에 설치하고자 한다면, [문서를 참조해라.](https://docs.jina.ai). 

⚠️ 윈도우 사용자들은 jina를 [윈도우상의 리눅스 하위 시스템](https://docs.jina.ai/chapters/install/via-pip.html?highlight=windows#on-windows-and-other-oses)을 통해 사용할 수 있다. 우리 커뮤니티는 [윈도우 지원](https://github.com/jina-ai/jina/issues/1252)에 대한 도움을 환영하고 있다.
 

### Docker 컨테이너

여러 아키텍쳐(x64, x86, arm-64/v7/v6을 포함)를 지원하는 범용적인 Docker 이미지를 제공한다. 아무것도 설치할 필요 없이, 그냥 수행하면 된다.

```bash
docker run jinaai/jina --help
```

## Jina "Hello, World!" 👋🌍

스타터로서, [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/)를 위한 이미지 신경 검색의 간단한 데모인 "Hello, World!"를 사용해보세요. 추가 종속성이 필요하지 않으며 다음을 실행하십시오.:

```bash
jina hello-world
```

...또는 Docker 사용자의 경우, **설치가 필요하지 않습니다.**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html  # replace "open" with "xdg-open" on Linux
```

<details>
<summary>콘솔 출력을 보려면 여기를 클릭하십시오.</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>

이것은 Fashion-MNIST 교육과 테스트 데이터 세트를 다운로드하고 지나에게 교육 세트에서 6만 개의 이미지를 인덱싱하라고 말한다. 그런 다음 검사 세트에서 무작위로 영상을 샘플링해 조회하고 지나에게 관련 결과를 가져오라고 한다. 전체 과정은 약 1분이 소요되며, 결과적으로 웹 페이지를 열고 다음과 같은 결과를 보여준다.

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

이면의 구현은 간단하다:

<table>
<tr>
<td> Python API </td>
<td> or use <a href="https://github.com/jina-ai/jina/blob/master/jina/resources/helloworld.flow.index.yml">YAML spec</a></td>
<td> or use <a href="https://github.com/jina-ai/dashboard">Dashboard</a></td>
</tr>
<tr>
<td>


```python
from jina.flow import Flow

f = (Flow()
        .add(uses='encoder.yml', parallel=2)
        .add(uses='indexer.yml', shards=2))

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
```

</td>
<td>

![대시보드의 흐름](https://github.com/jina-ai/jina/blob/master/docs/chapters/helloworld/hello-world-flow.png?raw=true)

</td>
</tr>
</table>

<details>
<summary><strong>샤딩, 컨테이너화, 임베딩 연결 등을 살펴보십시오.</strong></summary>

#### 병렬 및 샤딩 추가

```python
from jina.flow import Flow

f = (Flow().add(uses='encoder.yml', parallel=2)
           .add(uses='indexer.yml', shards=2))
```

#### [플로우 배포](https://docs.jina.ai/chapters/remote/index.html)

```python
from jina.flow import Flow

f = Flow().add(uses='encoder.yml', host='192.168.0.99')
```

#### [Docker 컨테이너 ](https://docs.jina.ai/chapters/hub/index.html)

```python
from jina.flow import Flow

f = (Flow().add(uses='jinahub/cnn-encode:0.1')
           .add(uses='jinahub/faiss-index:0.2', host='192.168.0.99'))
```

#### 연결 임베딩

```python
from jina.flow import Flow

f = (Flow().add(name='eb1', uses='BiTImageEncoder')
           .add(name='eb2', uses='KerasImageEncoder', needs='gateway')
           .needs(['eb1', 'eb2'], uses='_concat'))
```

#### [네트워크 쿼리 사용](https://docs.jina.ai/chapters/restapi/index.html)

```python
from jina.flow import Flow

f = Flow(port_expose=45678, rest_api=True)

with f:
    f.block()
```

흥미롭다면? 다른 옵션으로 재생하세요:

```bash
jina hello-world --help
```
</details>

### 첫 번째 Jina 프로젝트 생성하기

```bash
pip install jina[devel]
jina hub new --type app
```

하나의 터미널 명령으로 템플릿에서 쉽게 지나 프로젝트를 만들 수 있다. 이를 통해 Python 진입점, YAML 구성 및 Docker 파일이 생성된다. 그곳에서부터 귀하가 시작할 수 있다.


## 튜토리얼

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="https://github.com/jina-ai/jina/blob/master/docs/chapters/101/img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: First Things to Learn About Jina</a></h3>
&nbsp;&nbsp;<a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">English</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ja.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.fr.md">Français</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.pt.md">Português</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.de.md">Deutsch</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.zh.md">中文</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ar.md">عربية</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.kr.md">Korean</a>
    </td>

  </tr>
</table>

<table>
<tr>
<th width="10%">레벨</th>
<th width="90%">튜토리얼</th>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">NLP 의미 검색 시스템 구축</a></h4>
South Park의 문서를 검색하고 Flow와 Pods를 이용하여 연습해라
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/my-first-jina-app">내 첫 Jina 앱</a></h4>
Jina 앱을 bootstarp하기 위하여 cookiecutter를 사용
</td>
</tr>

<tr>
<td><h3>🐣</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/fashion-example-query">쿼리 언어를 사용한 패션 검색</a></h4>
쿼리 언어로 Hello-World에 활기 불어넣기
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/multires-lyrics-search">청크를 사용하여 가사 검색</a></h4>
Findgrained level에서 검색하기 위하여 문서를 쪼개기
</td>
</tr>

<tr>
<td><h3>🕊</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/cross-modal-search">이미지와 캡션을 믹스 앤 매치</a></h4>
이미지로부터 캡션 또는 캡션으로부터 이미지를 얻기 위하여 크로스 모달을 검색
</td>
</tr>

<tr>
<td><h3>🚀</h3></td>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">스케일업 비디오 의미 검색</a></h4>
프리패칭과 샤딩을 이용한 퍼포먼스의 향상
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

## 문서화

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="https://github.com/jina-ai/jina/blob/master/.github/jina-docs.png?raw=true " />
</a>

지나를 깊이 있게 배우는 가장 좋은 방법은 우리의 문서를 읽는 것이다. 문서는 마스터 브랜치의 모든 푸쉬, 머지, 릴리즈에 기초하여 작성된다.

#### 기본 사항

- [Flow API를 사용하여 검색 워크플로우 구성](https://docs.jina.ai/chapters/flow/index.html)
- [Jina의 입력 및 출력 기능](https://docs.jina.ai/chapters/io/index.html)
- [Dashboard를 사용하여 jina 워크플로우의 인사이트 확보](https://github.com/jina-ai/dashboard)
- [워크플로우를 원격으로 배포](https://docs.jina.ai/chapters/remote/index.html)
- [Docker Container를 통해 Jina 포드 실행](https://docs.jina.ai/chapters/hub/index.html)

#### 참조

- [command line 인터페이스 논의](https://docs.jina.ai/chapters/cli/index.html)
- [파이썬 API 인터페이스](https://docs.jina.ai/api/jina.html)
- [Executor과 Driver, Flow를 위한 VAML 문장](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Protobuf 스키마](https://docs.jina.ai/chapters/proto/index.html)
- [환경변수](https://docs.jina.ai/chapters/envs.html)
- ... [그 외](https://docs.jina.ai/index.html)

당신은 “DOC” 스타인가요? 우리와 함께해요! 우리는 문서에 대한 모든 종류의 개선을 환영합니다.

[이전 버전에 대한 설명서는 여기에 보관되어 있다.](https://github.com/jina-ai/docs/releases).

## 기여

우리는 오픈 소스 커뮤니티, 개인 및 파트너의 모든 종류의 기부를 환영한다. 우리의 성공은 당신의 적극적인 참여 덕분이다.

- [기여 지침](CONTRIBUTING.md)
- [릴리스 주기 및 개발 단계](RELEASE.md)

### 기부자 ✨

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![모든 기부자](https://img.shields.io/badge/all_contributors-74-orange.svg?style=flat-square)](#기부자-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->


<kbd><a href="https://jina.ai/"><img src="https://avatars1.githubusercontent.com/u/61045304?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://weizhen.rocks/"><img src="https://avatars3.githubusercontent.com/u/5943684?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/phamtrancsek12"><img src="https://avatars3.githubusercontent.com/u/14146667?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/gsajko"><img src="https://avatars1.githubusercontent.com/u/42315895?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://t.me/neural_network_engineering"><img src="https://avatars1.githubusercontent.com/u/1935623?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://hanxiao.io/"><img src="https://avatars2.githubusercontent.com/u/2041322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu-jina"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/nan-wang"><img src="https://avatars3.githubusercontent.com/u/4329072?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/tracy-propertyguru"><img src="https://avatars2.githubusercontent.com/u/47736458?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/maanavshah/"><img src="https://avatars0.githubusercontent.com/u/30289560?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/iego2017"><img src="https://avatars3.githubusercontent.com/u/44792649?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.davidsanwald.net/"><img src="https://avatars1.githubusercontent.com/u/10153003?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://alexcg1.github.io/"><img src="https://avatars2.githubusercontent.com/u/4182659?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/shivam-raj"><img src="https://avatars3.githubusercontent.com/u/43991882?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://dncc.github.io/"><img src="https://avatars1.githubusercontent.com/u/126445?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://johnarevalo.github.io/"><img src="https://avatars3.githubusercontent.com/u/1301626?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/imsergiy"><img src="https://avatars3.githubusercontent.com/u/8855485?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://guiferviz.com/"><img src="https://avatars2.githubusercontent.com/u/11474949?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rohan1chaudhari"><img src="https://avatars1.githubusercontent.com/u/9986322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/mohong-pan/"><img src="https://avatars0.githubusercontent.com/u/45755474?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/anish2197"><img src="https://avatars2.githubusercontent.com/u/16228282?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/joanna350"><img src="https://avatars0.githubusercontent.com/u/19216902?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/madhukar01"><img src="https://avatars0.githubusercontent.com/u/15910378?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/maximilianwerk"><img src="https://avatars0.githubusercontent.com/u/4920275?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/emmaadesile"><img src="https://avatars2.githubusercontent.com/u/26192691?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YikSanChan"><img src="https://avatars1.githubusercontent.com/u/17229109?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Zenahr"><img src="https://avatars1.githubusercontent.com/u/47085752?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JoanFM"><img src="https://avatars3.githubusercontent.com/u/19825685?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://yangboz.github.io/"><img src="https://avatars3.githubusercontent.com/u/481954?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/boussoffara"><img src="https://avatars0.githubusercontent.com/u/10478725?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/fhaase2"><img src="https://avatars2.githubusercontent.com/u/44052928?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Morriaty-The-Murderer"><img src="https://avatars3.githubusercontent.com/u/12904434?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rutujasurve94"><img src="https://avatars1.githubusercontent.com/u/9448002?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/theUnkownName"><img src="https://avatars0.githubusercontent.com/u/3002344?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/vltmn"><img src="https://avatars3.githubusercontent.com/u/8930322?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Kavan72"><img src="https://avatars3.githubusercontent.com/u/19048640?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bwanglzu"><img src="https://avatars1.githubusercontent.com/u/9794489?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/antonkurenkov"><img src="https://avatars2.githubusercontent.com/u/52166018?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/redram"><img src="https://avatars3.githubusercontent.com/u/1285370?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/ericsyh"><img src="https://avatars3.githubusercontent.com/u/10498732?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/festeh"><img src="https://avatars1.githubusercontent.com/u/6877858?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://julielab.de/Staff/Erik+F%C3%A4%C3%9Fler.html"><img src="https://avatars1.githubusercontent.com/u/4648560?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-jinaai"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/coolmian"><img src="https://avatars3.githubusercontent.com/u/36444522?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://www.joaopalotti.com/"><img src="https://avatars2.githubusercontent.com/u/852343?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.imxiqi.com/"><img src="https://avatars2.githubusercontent.com/u/4802250?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.cnblogs.com/callyblog/"><img src="https://avatars2.githubusercontent.com/u/30991932?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/rameshwara"><img src="https://avatars1.githubusercontent.com/u/13378629?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/alasdairtran"><img src="https://avatars0.githubusercontent.com/u/10582768?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="http://bit.ly/2UdLNBf"><img src="https://avatars2.githubusercontent.com/u/13751208?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/lusloher"><img src="https://avatars2.githubusercontent.com/u/64148900?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/pswu11"><img src="https://avatars2.githubusercontent.com/u/48913707?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://educatorsrlearners.github.io/portfolio.github.io/"><img src="https://avatars1.githubusercontent.com/u/17770276?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Showtim3"><img src="https://avatars3.githubusercontent.com/u/30312043?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/kaushikb11"><img src="https://avatars1.githubusercontent.com/u/45285388?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fernandakawasaki"><img src="https://avatars2.githubusercontent.com/u/50497814?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/clennan"><img src="https://avatars3.githubusercontent.com/u/19587525?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://sreerag-ibtl.github.io/"><img src="https://avatars2.githubusercontent.com/u/39914922?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/SirsikarAkshay"><img src="https://avatars1.githubusercontent.com/u/19791969?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/RenrakuRunrat"><img src="https://avatars3.githubusercontent.com/u/14925249?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/jyothishkjames"><img src="https://avatars0.githubusercontent.com/u/937528?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/JamesTang-616"><img src="https://avatars3.githubusercontent.com/u/69177855?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/Arrrlex"><img src="https://avatars1.githubusercontent.com/u/13290269?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/HelioStrike"><img src="https://avatars1.githubusercontent.com/u/34064492?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/bhavsarpratik"><img src="https://avatars1.githubusercontent.com/u/23080576?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/FionnD"><img src="https://avatars0.githubusercontent.com/u/59612379?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/fsal"><img src="https://avatars2.githubusercontent.com/u/9203508?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="http://stackoverflow.com/story/umbertogriffo"><img src="https://avatars2.githubusercontent.com/u/1609440?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/averkij"><img src="https://avatars0.githubusercontent.com/u/1473991?v=4" class="avatar-user" width="50px;"/></a></kbd>
<kbd><a href="https://github.com/jancijen"><img src="https://avatars0.githubusercontent.com/u/28826229?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://www.linkedin.com/in/deepankar-mahapatro/"><img src="https://avatars1.githubusercontent.com/u/9050737?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/dalekatwork"><img src="https://avatars3.githubusercontent.com/u/40423996?v=4" class="avatar-user" width="50px;"/></a></kbd> <kbd><a href="https://github.com/YueLiu1415926"><img src="https://avatars1.githubusercontent.com/u/64522311?v=4" class="avatar-user" width="50px;"/></a></kbd>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## community

- [Slack 작업영역](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - #장군에 합류하여 우리 슬랙을 팀원들과 만나 질문하다.
- [유튜브 채널](https://youtube.com/c/jina-ai) - 최신 비디오 튜토리얼, 릴리즈 데모, 웨비나 및 프리젠테이션을 구독하십시오.
- [링크드인](https://www.linkedin.com/company/jinaai/) - 지나 AI를 기업으로서 알게 되고 취업의 기회를 찾다.
- [![트위터 팔로우](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social)](https://twitter.com/JinaAI_) - 해시태그로 우리와 교류하다. `#JinaSearch`
- [회사](https://jina.ai) - 우리 회사에 대해 더 많이 알고 어떻게 우리가 오픈소스에 전념하고 있는지 알고 있다..

## 오픈 거버넌스

[깃허브 이정표](https://github.com/jina-ai/jina/milestones)로 Jina의 미래 개선점들에 대한 윤곽을 잡았음

여러분은 우리의 오픈 거버넌스 모델의 일환으로 모두를 위한 Jina의 공학을 주최한다.
Zoom미팅은 매달 두 번째 화요일마다 진행을 하며 시간은 14:00-15:30(CET)이다. Calendar 초대를 통해 모두 참여가 가능하다.

- [Google 캘린더에 추가](https://calendar.google.com/event?action=TEMPLATE&tmeid=MHIybG03cjAwaXE3ZzRrYmVpaDJyZ2FpZjlfMjAyMDEwMTNUMTIwMDAwWiBjXzF0NW9nZnAyZDQ1djhmaXQ5ODFqMDhtY200QGc&tmsrc=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&scp=ALL)
- [.ics다운로드 하기](https://hanxiao.io/2020/08/06/Engineering-All-Hands-in-Public/jina-ai-public.ics)

또한 이 회의는 생방송으로 송출될 것이며 이 후에 [유튜브 채널에 영상으로 제작될 것이다.](https://youtube.com/c/jina-ai).
## 참여하기

Jina는 오픈소스 프로젝트이다. 우리는 풀스택 개발자, evangelists, 프로젝트 매니저들을 [채용](https://jobs.jina.ai)하여 뉴럴 탐색 생태계를 오픈소스에 구축하려고 한다.

## 라이선스

Copyright (c) 2020 Jina AI Limited. All rights reserved

Jina는 Apache Licence 2.0을 사용한다. [라이선스 문서의 전문을 확인하기 위해서는 License를 참조하세요.](LICENSE)

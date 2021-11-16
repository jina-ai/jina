# 텍스트를 통해 비디오 내 시각적 콘텐츠 검색하세요

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 19, 2021
```

이 튜토리얼에서는 컨텐츠에 대한 짧은 텍스트 설명을 기반으로 비디오를 검색하는 비디오 검색 시스템을 만듭니다. 주요 과제는 사용자가 비디오에 대한 레이블이나 텍스트 정보를 사용하여  없이 비디오를 검색할 수 있도록 하는 것입니다.

<!--demo.gif-->
```{figure} ../../.github/images/tutorial-video-search.gif
:align: center
```

## flow 만드세요

사용할 수 있는 텍스트가 없기 때문에 쿼리 텍스트와 직접 일치시키기 위해 비디오의 텍스트 정보를 사용할 수 없습니다. 대신에, 우리는 비디오와 텍스트를 일치시킬 수 있는 다른 방법을 찾아야 합니다.
이러한 일치 항목을 찾는 한 가지 방법은 비디오 프레임에 있는 정보의 일부가 프레임에 캡처될 수 있기 때문에 비디오 프레임을 사용하는 것입니다. 좀 더 구체적으로 말하면, 쿼리 텍스트와 유사한 의미를 가진 관련 프레임을 찾은 다음 이러한 프레임을 포함하는 비디오를 반환할 수 있습니다. 이를 위해서는 모델이 비디오 프레임과 쿼리 텍스트를 동일한 공간에 인코딩해야 합니다. 이 경우 사전 훈련된 교차 모델들이 도움이 될 수 있습니다.

```{admonition} Use the other information of videos
:class: tip

일반적으로 비디오는 텍스트, 이미지, 오디오 등 세 가지 정보 소스를 포함합니다.
다른 출처의 정보 비율은 비디오마다 다릅니다.
이 예에서는 이미지 정보만 사용되며 프레임 이미지가 다음과 같이 가정됩니다.
비디오를 대표하며 사용자의 쿼리 요구에 부합할 수 있습니다.
즉, 이 예는 비디오에 다양한 프레임과 사용자가 포함된 경우에만 작동합니다.
텍스트를 사용하여 비디오 프레임을 검색해야 합니다.

비디오에 텍스트만 포함하거나 비디오에 정적 이미지가 하나만 있는 경우,
이 예는 잘 작동하지 않을 것입니다. 
그런 경우에 비디오의 주요 정보는 텍스트 또는 오디오로 표현되며, 따라서 비디오 프레임으로 검색할 수 없습니다.

이 튜토리얼의 또 다른 함정은 사용자가 이야기에 대한 설명과 함께 검색하기를 원할 수 있다는 것입니다.
예를 들어 파드메 아미달라와 C-3PO는 디트루우스 장군에 의해 인질로 잡힌다는 예시의 정보는 단일 프레임으로 설명할 수 없으며 쿼리는 비디오에 대한 추가 이해가 필요합니다.
이 튜토리얼의 범위를 벗어납니다.
```

### Executor를 선택하세요
비디오 프레임과 쿼리 텍스트를 동일한 공간에 인코딩하기 위해 OpenAI에서 사전 훈련된 [CLIP 모델](https://github.com/openai/CLIP)을 선택합니다.

```{admonition} What is CLIP?
:class: info

CLIP 모델은 자연 언어로부터 시각적 개념을 배우도록 훈련됩니다. 이 작업은 인터넷을 통해 텍스트 조각과 이미지 쌍을 사용하여 수행됩니다. 원래 CLIP 용지에서 모델은 텍스트 레이블과 이미지를 분리된 모델로 인코딩하여 Zero Shot 학습을 수행합니다. 나중에 인코딩된 벡터 간의 유사성이 계산됩니다. 
```

이 튜토리얼에서는 CLIP의 이미지와 텍스트 인코딩 부분을 사용하여 임베딩을 계산합니다.

```{admonition} How does CLIP help?
:class: info

짧은 텍스트 'this is a dog'가 주어지면 CLIP 텍스트 모델은 이를 벡터로 인코딩할 수 있습니다. 반면, CLIP 이미지 모델은 개의 이미지 하나와 고양이의 이미지 하나를 동일한 벡터 공간으로 인코딩할 수 있습니다.
또한 우리는 텍스트 벡터와 개 이미지 벡터 사이의 거리가, 동일한 텍스트와 고양이의 이미지 사이의 거리보다 더 작다는 것을 알 수 있습니다.
```

인덱서의 경우 시연용이라는 점을 고려해 인덱서로 `SimpleIndexer` 를 선택합니다. 벡터와 메타 정보를 모두 한번에 저장합니다. 검색 파트는 `DocumentArrayMemmap` 의 내장된 `match` 기능을 사용하여 수행됩니다.

## Go through the Flow
이 예에서 정의한 Flow는 하나만 있지만 Executors에 대한 `requests` 데코레이터를 설정하여 `/index` 및 `/search`에 대한 요청을 다르게 처리합니다. 

```{figure} ../../.github/images/tutorial-video-search.png
:align: center
```

### 인덱스
인덱스 엔드포인트에 대한 요청은 `Videoloader`, `CLIPImageEncoder`, `SimpleIndexer` 3개의 Executor가 있습니다. Flow에 대한 입력은 동영상 URI가 `uri` 속성에 저장된 문서입니다. 클라우드 또는 로컬 파일 시스템의 원격 파일 위치입니다.

`VideoLoader` 는 영상에서 프레임을 추출해 청크의 `blob` 속성에 이미지 배열로 저장합니다.

`VideoLoader` 이후의 문서 형식은 다음과 같습니다:

```{figure} ../../.github/images/tutorial-video-search-doc.jpg
:align: center
```


두 번째 단계인 `CLIPImageEncoder` 는 이미지에 대한 CLIP 모델을 기반으로 각 청크에 대한 `embedding` 속성을 계산합니다. 결과 벡터는 512차원입니다.   

### Query

`/search` 엔드포인트에 게시되면 `CLIPTextEncoder`, `SimpleIndexer` 그리고 `SimpleRanker`를 통해 요청이 들어옵니다.
이러한 요청에는 문서의 `text` 속성에 저장된 텍스트 설명이 있습니다. 이러한 텍스트는 `CLIPTextEncoder` 에 의해 벡터로 인코딩됩니다. 벡터는 `embedding` 속성에 저장되며 `SimpleRanker` 를 사용하여 비디오 프레임의 관련 벡터를 검색하는 데 사용됩니다. 마지막으로  `SimpleRanker` 는 검색된 프레임을 기반으로 해당 동영상을 찾습니다.

### Jina Hub에서 Executor 사용하기

`SimpleRanker` 를 제외하고 이 튜토리얼에 사용된 다른 모든 실행기는 [hub.jina.ai](https://hub.jina.ai/))에서 사용할 수 있습니다. 

- [`VideoLoader`](https://hub.jina.ai/executor/i6gp4vwu)
- [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q)
- [`CLIPTextEncoder`](https://hub.jina.ai/executor/livtkbkg)
- [`SimpleIndexer`](https://hub.jina.ai/executor/zb38xlt4)

기본적으로 `CLIPImageEncoder` 는 루트 수준에서 문서의 `blob` 을 인코딩합니다. 이 예에서 루트 수준의 문서는 비디오를 나타내고 청크는 CLIP 모델이 인코딩해야 하는 비디오 프레임을 나타냅니다. YAML 파일에서 이 기본 구성을 재정의하기 위해 `uses_with` 필드에서 `traversal_paths: ['c']` 를 설정합니다. 루트 수준에서 문서를 인코딩하는 대신 임베딩은 각 청크의 `blob` 을 기준으로 계산됩니다.

```{code-block} yaml
---
emphasize-lines: 5, 6
---
...
executors:
  ...
  - uses: jinahub://CLIPImageEncoder/v0.1
    uses_with:
      traversal_paths: ['c',]
...
```

### Override requests configuration
`traversal_paths` 를 오버라이딩하는 것과 마찬가지로, `/index` 와 `/search` 엔드포인트에 대한 요청이 예상대로 처리될 수 있도록 `@requests` 를 구성해야 합니다. `VideoLoader` 와 `CLIPImageEncoder` 는 인덱스 엔드포인트에 대한 요청만 처리합니다. 반면 `CLIPTextEncoder` 는 엔드포인트에 대한 `/search` 요청만 처리합니다.


```{code-block} yaml
---
emphasize-lines: 5, 6, 9, 10, 13, 14
---
...
executors:
  - uses: jinahub://VideoLoader/v0.2
    ...
    uses_requests:
      /index: 'extract'
  - uses: jinahub://CLIPImageEncoder/v0.1
    ...
    uses_requests:
      /index: 'encode'
  - uses: jinahub://CLIPTextEncoder/v0.1
    ...
    uses_requests:
      /search: 'encode'
...
```

## 소스 코드를 얻으세요

당신은 [example-video-search](https://github.com/jina-ai/example-video-search)에서 코드를 찾을 수 있습니다. 

# Question-Answering on in-Video Content

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 24, 2021
```


질문을 하는 것은 검색을 수행하는 자연스러운 방법입니다. 지나에 있는 문서의 정의를 알고 싶을 때, 자연스럽게 "__지나에 있는 문서는 무엇입니까?  예상 답변은 [지나스 문서](https://docs.jina.ai/))나 [지나스 유튜브 채널](https://www.youtube.com/c/JinaAI))의 소개 영상에서 확인할 수 있습니다. NLP의 최신 발전 덕분에, AI 모델은 콘텐츠에서 이러한 답을 자동으로 찾을 수있습니다.

이 튜토리얼의 목적은 비디오 콘텐츠에 대한 질의응답(QA) 시스템을 구축하는 것입니다. 대부분의 기존 QA 모델은 텍스트에만 사용되지만, 우리 삶의 대부분의 비디오는 비디오에 대한 풍부한 정보를 포함하고 [STT](https://en.wikipedia.org/wiki/Speech_recognition))를 통해 텍스트로 변환할 수 있는 음성을 가지고 있습니다. 그 이후, 연설이 포함된 비디오는 자연스럽게 텍스트를 통한 질의응답에 일치합니다.

이 튜토리얼에서는 쿼리 질문에 대답하는 비디오에서 콘텐츠를 찾고 추출하는 방법을 보여 줍니다.
QA 모델은 사용자가 관련 비디오를 찾아 전체 비디오를 훑어보는 대신 질문에 대한 답을 얻기 위해 몇 초부터 시작해야 하는지 사용자에게 알려줄 수 있습니다.

```{figure} ../../.github/images/tutorial-video-qa.gif
:align: center
```

## FLow를 만드세요

동영상의 음성 정보를 텍스트로 변환하기 위해 STT 알고리즘에 의존할 수 있습니다. 다행스럽게도, 대부분
유튜브(https://support.google.com/youtube/answer/6373554)의 동영상?hl=en), STT를 통해 자동으로 생성되는 자막을 다운로드할 수 있습니다. 이 예에서는, 우리는
비디오 파일에는 이미 자막이 포함되어 있습니다. 이 자막들을 로드함으로써, 우리는 연설의 본문을 함께 얻을 수 있습니다.
시작 타임스탬프와 끝 타임스탬프가 함께 표시됩니다

```{admonition} Tips
:class: info

You can use `youtube-dl` to download YouTube videos with embedded subtitles:

:::text
youtube-dl --write-auto-sub --embed-subs --recode-video mkv -o zvXkQkqd2I8 https://www.youtube.com/watch\?v\=zvXkQkqd2I8
:::
```

```{admonition} Note
:class: important



STT로 생성된 자막은 100% 정확하지 않습니다. 일반적으로 자막을 후처리해야 합니다. 예를 들어, 
장난감 자료에서, 우리는 지나 소개 비디오를 사용합니다. 자동 생성된 자막에서 지나는 gena로 철자가 틀렸습니다.
심지어, 대부분의 문장들이 깨지고 구두점이 없습니다.
```


동영상의 자막과 함께, 우리는 QA 모델이 더 필요합니다. QA 모델에 대한 입력에는 일반적으로 두 가지 부분이 있습니다.
the question 과 the context the question 은 답이 포함된 후보 텍스트를 나타냅니다. 그리고  the context은 답이 추출되는 자막과 일치합니다.

계산 비용을 절약하기 위해 가능한 한 짧은 the context 을 갖기를 원합니다. 그러한 the context를 생성하기 위해, 전통적인 정보 희소 벡터 또는 고밀도 벡터를 사용할 수 있습니다. 이 예에서는 QA 모델과 함께 제공되는 조밀 벡터를 사용하기로 결정했습니다.


```{admonition} Note
:class: info

With traditional methods, retrieval can also be done using BM25, Tf-idf, etc.
```

### 실행기를 선택하세요


비디오로더(VideoLoader)를 이용해 동영상에서 자막을 추출합니다. [ffmpeg](https://www.ffmpeg.org/)을 이용해 자막을 추출합니다.
그런 다음 [webvtt-py](https://github.com/glut23/webvtt-py))를 사용하여 자막을 기반으로 `chunks` 를 생성합니다. 자막은 `chunks` `chunks` 에 저장돼 있습니다.
타임스탬프 및 동영상 정보 등 '메타'에 있는 다른 메타 정보와 함께. 추출된 자막에는 다음과 같은 특성이 있습니다.

| tags | information |
| -- | ---- |
| `text` | Text of the subtitle |
| `location` | Index of the subtitle in the video, starting from `0` |
| `modality` | always set to `text` |
| `tags['beg_in_seconds']` | Beginning of the subtitle in seconds |
| `tags['end_in_seconds']` | End of the subtitle in seconds |
| `tags['video_uri']` | URI of the video |

QA 모델에서 , 우리는 [`Dense Passage Retrieval (DPR)`](https://huggingface.co/transformers/model_doc/dpr.html) models을 선택할 수 있습니다. 구성은 다음과 같습니다:

- 질문과 답변을 동일한 공간에서 벡터로 인코딩하는 임베딩 모델입니다. 이렇게 하면 답이 포함될 가능성이 가장 높은 후보 문장을 검색할 수 있습니다.
- 후보 문장에서 정확한 답을 추출하는 독자 모델이 있습니다.

```{admonition} Note
:class: info

`DPR` is a set of tools and models for open domain Q&A tasks.
```

For the indexer, we choose `SimpleIndexer` for demonstration purposes. It stores both vectors and meta-information together. You can find more information on [Jina Hub](https://hub.jina.ai/executor/zb38xlt4)

##  the Flow를 통과하세요
인덱싱 및 쿼리 흐름에는 공유 실행자가 하나만 있기 때문에 각 작업에 대해 별도의 the Flow가 생성됩니다.

### Index

인덱스 요청에는 동영상 파일의 경로 정보가 'uri' 속성에 저장된 문서가 포함됩니다.

index flow에서는 3개의 excuter가 있습니다:

- `VideoLoader` 자막들을 추출하고 그들을 `chunks`에 저장합니다. 다큐먼트의 'chunks'는  `text` attribute에 저장된 하나의 자막을 가집니다. 
- `DPRTextEncoder` 벡터로 자막을 인코딩합니다.
- `SimpleIndexer` 벡터들과 다른 메타 정보를 저장합니다.


```{figure} ../../.github/images/tutorial-video-qa-flow-index.png
:align: center
```

### Query

Query flow에서는 4개의 excuter가 있습니다:

- 'DPRTextEncoder'는 쿼리 문서의 '텍스트' 속성에 저장된 질문을 가져와서 벡터로 인코딩합니다. 
- 'SimpleIndexer'는 벡터 공간에서 가장 가까운 이웃을 찾아 관련 자막을 검색다. 검색된 결과는 쿼리 문서의 '매치' 속성에 저장됩니다. 매치의 각 문서에는 심플인덱서로 검색되는 자막에 대한 메타 정보와 자막 텍스트도 모두 담겨 있습니다.
- DJReaderRanker는 질문과 후보 자막을 이용해 정확한 답을 찾습니다. 문항과 후보 자막은 각각 문서의 텍스트 속성과 매치에 저장됩니다. 기존의 매치를 대체한 디프리더랭커는 매치의 텍스트 속성에 가장 잘 맞는 답을 저장한다. 이와 같이 태그['beg_in_seconds]와 태그['video_uri]를 포함한 다른 메타 정보도 새로운 일치 항목에 복사됩니다. 
- 'ThepredrRanker'는 두 가지 스코어를 반환합니다. 점수(scores['revelance_score')는 답을 추출하는 자막의 문제와의 관련성을 측정합니다. 점수란 자막 중 추출한 답의 가중치를 뜻합니다.
-'Text2frame'은 검색된 답변에서 동영상 프레임 정보를 가져와 맨 앞에 표시할 문서를 준비합니다.

 
The overall structure of the query Flow is as follows:

```{figure} ../../.github/images/tutorial-video-qa-flow-query.png
:align: center
```

###`DPRTextEncoder`를 두개의 flow에서 다르게 사용하세요

'DPRTextEncoder'가 인덱스 및 쿼리 flow 모두에서 사용될 수 있습니다.

- index  부제 텍스트를 인코딩합니다.
- query flow에서 쿼리 질문을 인코딩합니다.

이 두 경우 문서의 다른 속성을 인코딩하기 위해 다른 모델을 선택해야 합니다. 이를 위해 YAML 파일에서 with 인수를 재정의하여 'DPRTextEncoder'에 대해 서로 다른 초기화 설정을 사용합니다. 그러기 위해서는 새로운 주장을 'uses_with'로 넘겨야 합니다. 자세한 내용은 [지나 문서](https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/#pature-with-configuration)에서 확인할 수 있습니다.
```{code-block} YAML
---
emphasize-lines: 5, 6, 7, 8, 9
---
  # index.yml
  ... 
  - name: encoder
    uses: jinahub://DPRTextEncoder/v0.2
    uses_with:
      pretrained_model_name_or_path: 'facebook/dpr-ctx_encoder-single-nq-base'
      encoder_type: 'context'
      traversal_paths:
        - 'c'
  ...
```

```{code-block} YAML
---
emphasize-lines: 5, 6, 7, 8
---
  # query.yml
  ... 
  - name: encoder
    uses: jinahub://DPRTextEncoder/v0.2
    uses_with:
      pretrained_model_name_or_path: 'facebook/dpr-question_encoder-single-nq-base'
      encoder_type: 'question'
      batch_size: 1
  ...
```

## 소스 코드를 얻으세요

코드는 [video-video-qa](https://github.com/jina-ai/example-video-qa)에서 확인할 수 있습니다.

이 튜토리얼에 사용된 대부분의 실행기는 지나 허브에서 사용할 수 있습니다.

- [`VideoLoader`](https://hub.jina.ai/executor/i6gp4vwu)
- [`DPRTextEncoder`](https://hub.jina.ai/executor/awl0jxog)
- [`DPRReaderRanker`](https://hub.jina.ai/executor/gzhiwmgg)
- [`SimpleIndexer`](https://hub.jina.ai/executor/zb38xlt4)


## 다음 단계

이 예에서는 비디오에 포함된 자막에 의존합니다. 자막이 없는 동영상의 경우 음성 정보를 추출하기 위해 STT 모델을 사용하여 실행기를 만들어야 합니다. 비디오에 다른 소리가 포함된 경우, [VADSpeechSegmenter](https://hub.jina.ai/executor/9sohw4wi))를 사용하여 미리 음성을 분리할 수 있습니다.

이 예제를 확장하는 또 다른 방향은 동영상의 다른 텍스트 정보를 고려하는 것입니다. 자막에는 동영상에 대한 풍부한 정보가 포함되어 있지만 모든 텍스트 정보가 자막에 포함되는 것은 아닙니다. 많은 비디오에는 이미지에 텍스트 정보가 포함되어 있습니다. 이러한 경우 비디오 프레임에서 텍스트 정보를 추출하기 위해 OCR 모델에 의존해야 합니다.

전반적으로, 비디오 콘텐츠를 검색하는 것은 복잡한 작업이고 Jina는 그것을 훨씬 더 쉽게 만들어 줍니다.

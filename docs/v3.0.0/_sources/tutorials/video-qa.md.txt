# Question-Answering on in-Video Content

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 24, 2021
```


Asking questions is a natural way to perform a search. When you want to know the definition of Document in Jina, you will naturally ask, "__What is the Document in Jina?__". The expected answer can be found either from [Jina's docs](https://docs.jina.ai/) or the introduction videos on [Jina's YouTube channel](https://www.youtube.com/c/JinaAI). Thanks to the latest advances in NLP, AI models can automatically find these answers from the content.

The goal of this tutorial is to build a Question-Answering (QA) system for video content. Although most existing QA models only work for text, most videos in our life have speech which contains rich information about the video and can be converted to text via [speech recognition (STT)](https://en.wikipedia.org/wiki/Speech_recognition). Thereafter, videos with speech naturally fit question-answering via text.

In this tutorial, we will show you how to find and extract content from videos that answers a query question. 
Instead of just finding related videos and having the user skim through the whole video, QA models can tell the user which second they should start from to get the answer to their question.

```{figure} ../../.github/images/tutorial-video-qa.gif
:align: center
```

## Build the Flow
To convert speech information from the videos into text, we can rely on STT algorithms. Fortunately, for most 
videos on [YouTube](https://support.google.com/youtube/answer/6373554?hl=en), you can download the subtitles that are generated automatically via STT. In this example, we assume
the video files already have subtitles embedded. By loading these subtitles, we can get the text of the speech together
with the beginning and ending timestamps.

```{admonition} Tips
:class: info

You can use `youtube-dl` to download YouTube videos with embedded subtitles:

:::text
youtube-dl --write-auto-sub --embed-subs --recode-video mkv -o zvXkQkqd2I8 https://www.youtube.com/watch\?v\=zvXkQkqd2I8
:::
```

```{admonition} Note
:class: important

Subtitles generated with STT are not 100% accurate. Usually, you need to post-process the subtitles. For example, in 
the toy data, we use an introduction video of Jina. In the auto-generated subtitles, `Jina` is misspelled as `gena`, 
`gina`, etc. Worse still, most of the sentences are broken and there is no punctuation. 
```

With the subtitles of the videos, we further need a QA model. The input to the QA model usually has two parts:
the question and the context. The context denotes the candidate texts that contain the answers. In our case, the context corresponds to the subtitles from which the answers are extracted. 

To save computational cost, we want to have the context as short as possible. To generate such contexts, one can use either traditional information sparse vectors or dense vectors. In this example, we decide to use the dense vectors that are shipped together with the QA model.


```{admonition} Note
:class: info

With traditional methods, retrieval can also be done using BM25, Tf-idf, etc.
```

### Choose Executors

We use `VideoLoader` to extract subtitles from the videos. It uses [`ffmpeg`](https://www.ffmpeg.org/) to extract subtitles 
and then generates chunks based on the subtitles using [`webvtt-py`](https://github.com/glut23/webvtt-py). The subtitles are stored in the `chunks` 
together with other meta-information in the `tags`, including timestamp and video information. Extracted subtitles have the following attributes:

| tags | information |
| -- | ---- |
| `text` | Text of the subtitle |
| `location` | Index of the subtitle in the video, starting from `0` |
| `modality` | always set to `text` |
| `tags['beg_in_seconds']` | Beginning of the subtitle in seconds |
| `tags['end_in_seconds']` | End of the subtitle in seconds |
| `tags['video_uri']` | URI of the video |

For the QA model, we choose the [`Dense Passage Retrieval (DPR)`](https://huggingface.co/transformers/model_doc/dpr.html) models that were originally proposed by [Facebook Research](https://github.com/facebookresearch/DPR). These consist of:

- An embedding model to encode the questions and answers into vectors in the same space. This way, we can retrieve candidate sentences that are most likely to contain the answer. 
- A reader model that extracts exact answers from candidate sentences.

```{admonition} Note
:class: info

`DPR` is a set of tools and models for open domain Q&A tasks.
```

For the indexer, we choose `SimpleIndexer` for demonstration purposes. It stores both vectors and meta-information together. You can find more information on [Jina Hub](https://hub.jina.ai/executor/zb38xlt4)

## Go through the Flow
Because the indexing and querying Flows have only one shared Executor, we create separate Flows for each task.

### Index

The index request contains Documents that have the path information of the video files stored in their `uri` attribute.

There are three Executors in the index Flow:

- `VideoLoader` extracts the subtitles and stores them in `chunks`. Each chunk of the Document has one subtitle stored in its `text` attribute. 
- `DPRTextEncoder` encodes the subtitles into vectors.
- `SimpleIndexer` stores the vectors and other meta-information


```{figure} ../../.github/images/tutorial-video-qa-flow-index.png
:align: center
```

### Query

There are four Executors in the query Flow:

- `DPRTextEncoder` takes the question stored in the `text` attribute of the query Document and encodes it into a vector. 
- `SimpleIndexer` retrieves related subtitles by finding the nearest neighbours in the vector space. The retrieved results are stored in the `matches` attribute of the query Document. Each Document in the `matches` also has all the meta-information about the subtitles, which is retrieved by `SimpleIndexer` together with subtitle text.
- `DPRReaderRanker` finds exact answers by using the question and the candidate subtitles. The question and candidate subtitles are stored in the `text` attributes of the Document and its `matches` respectively. Replacing the existing `matches`, the `DPRReaderRanker` stores the best-matched answers in the `text` attribute of the `matches`. Other meta-information is also copied into the new matches, including `tags['beg_in_seconds']`, `tags['end_in_seconds']`, and `tags['video_uri']`. The `DPRReaderRanker` returns two types of `scores`. The `scores['relevance_score']` measures the relevance to the question of the subtitle from which the answer is extracted. The `scores['span_score']` indicates the weight of the extracted answer among the subtitles.
- `Text2Frame` gets the video frame information from the retrieved answers and prepares the Document `matches` for displaying in the frontend. 
 
The overall structure of the query Flow is as follows:

```{figure} ../../.github/images/tutorial-video-qa-flow-query.png
:align: center
```

### Use `DPRTextEncoder` differently in two Flows

You might note that `DPRTextEncoder` is used in both the index and query Flows:

- In the index Flow it encodes subtitle text
- In the query Flow it encodes query questions
 
In these two cases, we need to choose different models to encode the different attributes of the Documents. To achieve this, we use different initialization settings for `DPRTextEncoder` by overriding the `with` arguments in the YAML file. To do this, we need to pass the new argument to `uses_with`. You can find more information in [Jina's docs](https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/#override-with-configuration).


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

## Get the Source Code

You can find the code at [example-video-qa](https://github.com/jina-ai/example-video-qa).

Most of the Executors used in this tutorial are available on Jina Hub:

- [`VideoLoader`](https://hub.jina.ai/executor/i6gp4vwu)
- [`DPRTextEncoder`](https://hub.jina.ai/executor/awl0jxog)
- [`DPRReaderRanker`](https://hub.jina.ai/executor/gzhiwmgg)
- [`SimpleIndexer`](https://hub.jina.ai/executor/zb38xlt4)


## Next Steps

In this example, we rely on subtitles embedded in the video. For videos without subtitles, we need to build Executors using STT models to extract speech information. If the video contains other sounds, you can resort to [VADSpeechSegmenter](https://hub.jina.ai/executor/9sohw4wi) for separating speech beforehand.

Another direction to extend this example is to consider the videos' other text information. While subtitles contain rich information about the video, not all text information is included in subtitles. A lot of videos have text information embedded in images. In such cases, we need to rely on OCR models to extract text information from the video frames. 

Overall, searching in-video content is a complex task and Jina makes it a lot easier.

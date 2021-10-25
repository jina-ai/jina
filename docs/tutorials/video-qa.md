# Build a Question-Answering System for in-Video Contents

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 24, 2021
```


As a way of searching, asking questions is a natural way to perform searching. For example, when you want to know the definition of Document in Jina, you will naturally ask, "__What is the Document in Jina?__". The expected answer can be found either from the documentation of Jina or the introduction videos at our YouTube channel. Thanks to the latest advances in NLP, the AI models can automatically find these answers from the contents. 

The goal of this tutorial is to build a Question-Answering (QA) system for in-Video Contents. Although most of the existing QA models only work for text, most videos in our life have vocal sound which contains rich information about the video and can be converted into text via __STT__. Thereafter, videos with vocal sound naturally fits to the way of Question-Answering via text.

In this tutorial, we will show you how to find the extract contents from videos that answer the question. 
Instead of returning the related videos, the QA models can tell the user from which second to watch in order to get the answer to the question.

```{figure} ../../.github/images/tutorial-video-qa.gif
:align: center
```

## Build the Flow
To convert vocal information of the videos into texts, we can rely on STT algorithms. Fortunately, for most of the
videos at YouTube, one can download the subtitles that are generated automatically via STT. In this example, we assume
the video files have subtitles already embedded. By loading the subtitles, we can get the texts of the vocal sounds together
with the beginning and ending timestamp.

```{admonition} Tips
:class: info

You can use `youtube-dl` to download the YouTube videos with subtitles embedded via

:::text
youtube-dl --write-auto-sub --embed-subs --recode-video mkv -o zvXkQkqd2I8 https://www.youtube.com/watch\?v\=zvXkQkqd2I8
:::
```

```{admonition} Note
:class: important

The subtitles generated via STT are not 100% precise. Usually, you need to post-process the subtitles. For example, in 
the toy-data, we use an introduction video of Jina. In the auto-generated subtitles, `jina` is mis-spelled into `gena`, 
`gina` and etc. Worsestill, most of the sentences are broken and there is no punctuation. 
```

With the subtitles of the videos, we further need a QA model. The input to the QA model usually has two parts, namely 
the question and the context. The context denotes the candidate texts that contain the answers. To save the 
computation cost, we want to have the context as short as possible. To generate such contexts, one can use either traditional information sparse vectors or dense vectors. In this example, we decide to use the dense vectors that are shipped together with the QA model.


```{admonition} Note
:class: info

With the traditional methods, the retrieval part can also be done via using BM25, Tf-idf and etc.
```

### Choose Executors

To extract the subtitles from the videos, we use `VideoLoader` to extract. It uses `ffmpeg` to extract the subtitles 
and afterwards generated chunks based on the subtitles with `webvtt-py`. The subtitles are stored in the `chunks` 
together with the timestamp information and the video information at `tags`. The extracted subtitles have the following attributes, 

| tags | information |
| -- | ---- |
| `text` | the text of the subtitle |
| `location` | the index of the subtitle in the video, starting from `0` |
| `modality` | always set to `text` |
| `tags['beg_in_seconds']` | the beginning of the subtitle in seconds |
| `tags['end_in_seconds']` | the end of the subtitle in seconds |
| `tags['video_uri']` | the uri of the video |

For the QA model, we choose the [`Dense Passage Retrieval (DPR)`](https://huggingface.co/transformers/model_doc/dpr.html) models that are originally proposed by [Facebook Research](https://github.com/facebookresearch/DPR). It consists of two parts. The first part is an embedding model to encode the questions and answers into vectors that in the same space. With the first part, we can retrieve the candidate sentences that are most likely to contain the answer. The second part is a reader model that can extract the exact answers from the candidate sentences.

```{admonition} Note
:class: info

`DPR` is a set of tools and models for open domain Q&A task.
```

As for the indexer, we choose `SimpleIndexer` for demonstration purposes. It stores both vectors and meta-information at the same time. You can find more information at [hub.jina.ai](https://hub.jina.ai/executor/zb38xlt4)

## Go through the Flow
As the indexing and querying flows have only one shared executor, we create seperated flows for them.

### Index

<!--index.png-->

### Query

<!--query.png-->

## Get the Source Code

You can find the codes at [example-video-qa](https://github.com/jina-ai/example-video-qa).
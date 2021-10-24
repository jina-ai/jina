# Build a Question-Answering System for in-Video Contents

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 24, 2021
```

The goal of this tutorial is to build a Question-Answering example for in-Video Contents. 
The most of videos in our life have vocal sound which contains rich information about the video. 
As the vocal sounds can be converted into text via __STT__, vocal sound naturally fits to the way of searching via text.
From the other way, asking questions is a typical way of searching. With the latest advances in NLP, we can enable the users to ask question about the video and find the extract timestamps that answer the question.
Instead of returning the related videos, the advances in the QA field can tell you which second to watch in order to get the answer to the question.

```{figure} ../../.github/images/tutorial-video-qa.gif
:align: center
```

## Build the Flow

The goal of the example is to enable the user to ask questions in natural languages and retrieve the related video segments containing answers. On the other hand, the models in Question-Answering field are designed to extract answers from the text. To fill this gap, we choose to extract the vocal sounds using STT algorithms. 
Fortunately, for most of the videos at YouTube, one can download the subtitles that are generated automatically via STT. 
In this example, we assume the video files have subtitles embedded. By loading the subtitles, we can get the texts of the vocal sounds together with the begining and ending timestamp.

```{admonition} Note
:class: important

The subtitles generated via STT are not 100% precise. Usually, you need to post-process the subtitles. For example, in 
the toy-data, we use an introduction video of Jina. In the auto-generated subtitles, `jina` is mis-spelled into `gena`, 
`gina` and etc. Worsestill, most of the sentences are broken and there is no punctuation. 
```

With the subtitles of the videos, we further need a QA model. The input to the QA model usually has two parts, namely 
the question and the context. The context denotes the candidate texts that contains the answers. To save the 
computation cost, we want to have the context as short as possible. To generate such contexts, one can use either traditional information sparse vectors or dense vectors. In this example, we decide to use the dense vectors that are shipped together with the QA model.


### Choose Executors

To extract the subtitles from the videos, we use `VideoLoader` to extract. It uses `ffmpeg` to extract the subtitle file 
and afterwards generated chunks based on the subtitles with `webvtt-py`. The subtitles are stored in the `chunks` 
together with the timestamp information and the video information at `tags`.

<!--table_to_show_the_chunks-->

For the QA model, we choose the [`Dense Passage Retrieval (DPR)`](https://huggingface.co/transformers/model_doc/dpr.html) models that are originally proposed by [Facebook Research](https://github.com/facebookresearch/DPR). It consists of two parts. The first part is an embedding model to encode the questions and answers into vectors that in the same space. With the first part, we can retrieve the candidate sentences that are most likely to contain the answer. The second part is a reader model that can extract the exact answers from the candidate sentences.

```{admonition} Note
:class: info

`DPR` is a set of tools and models for open domain Q&A task.
```

As for the indexer, we choose `SimpleIndexer` for demonstration purposes. It stores both vectors and meta-information in
one shot. You can find more information at [hub.jina.ai](https://hub.jina.ai/executor/zb38xlt4)

## Go through the Flow
As the indexing and querying flows have only one shared executor, we create seperated flows for them.

### Index

<!--index.png-->

### Query

<!--query.png-->


# Search in-Video Visual Content via Text

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 19, 2021
```

In this tutorial, we create a video search system that retrieves videos based on short text descriptions of their content. The main challenge is to let the user search videos _**without**_ using any labels or text information about the videos.

<!--demo.gif-->
```{figure} ../../.github/images/tutorial-video-search.gif
:align: center
```

## Build the Flow

Given that there is no text available, we cannot use the text information of the video to match the query text directly. Instead, we need to figure out another way to match videos and texts. 
One way to find such matches is to use the video frames because part of the information in the videos can be captured in the frames. To be more concrete, we can find related frames with similar semantics to the query texts and then return the videos containing these frames. This requires models to encode the video frames and the query texts into the same space. In this case, pre-trained cross-modal models can help us out.

```{admonition} Use the other information of videos
:class: tip

Generally, videos contain three sources of information, namely text, image, and audio. 
The ratio of information from different sources varies from video to video. 
In this example, only the image information is used and this assumes that the frame images are 
representative of the video and can match the user's query needs. 
In other words, this example only works when a video contains various frames and the user
needs to search the video frames using text. 

If a video only contains text or a video only has a single static image, 
this example won't work well. In such cases,
 the main information of the video is represented by either text or audio and therefore cannot
 be searchable with the video frames. 

Another pitfall of this tutorial is that the user might want to search with a description of 
the story, for example, `Padmé Amidala and C-3PO are taken hostage by General Grievous`. 
This information cannot be described by a single frame and the query needs further understanding of 
the video. This is beyond the scope of this tutorial.
```

### Choose Executors
To encode video frames and query texts into the same space, we choose the pre-trained [CLIP model](https://github.com/openai/CLIP) from OpenAI. 

```{admonition} What is CLIP?
:class: info

The CLIP model is trained to learn visual concepts from natural languages. This is done using text snippets and image pairs across the internet. In the original CLIP paper, the model performs Zero Shot Learning by encoding text labels and images with separated models. Later the similarities between the encoded vectors are calculated . 
```

In this tutorial, we use the image and the text encoding parts from CLIP to calculate the embeddings. 

```{admonition} How does CLIP help?
:class: info

Given a short text `this is a dog`, the CLIP text model can encode it into a vector. Meanwhile, the CLIP image model can encode one image of a dog and one image of a cat into the same vector space.
We can further find the distance between the text vector and the vectors of the dog image is smaller than that between the same text and an image of a cat. 
```

For the indexer, considering this is for demonstration purposes, we choose `SimpleIndexer` as our indexer. It stores both vectors and meta-information in one shot. The search part is done using the built-in `match` function of `DocumentArrayMemmap`.

## Go through the Flow
Although there is only one Flow defined in this example, it handles requests to `/index` and `/search` differently by setting the `requests` decorators for the Executors:

```{figure} ../../.github/images/tutorial-video-search.png
:align: center
```

### Index
For requests to the `/index` endpoint, there are three Executors involved: `VideoLoader`, `CLIPImageEncoder` and `SimpleIndexer`. The inputs to the Flow are Documents with video URIs stored in the `uri` attribute. They are the file locations either remotely on the cloud or in your local filesystem. 

The `VideoLoader` extracts the frames from the video and stores them as image arrays in the `blob` attribute of the chunks. 

The Documents after `VideoLoader` have the following format:

```{figure} ../../.github/images/tutorial-video-search-doc.jpg
:align: center
```


As the second step, `CLIPImageEncoder` calculates the `embedding` attribute for each chunk based on the CLIP model for images. The resulting vectors are 512-dimensional. 


Afterwards, `SimpleIndexer` stores all the Documents with a memory map.  

### Query

When being posted to the `/search` endpoint, requests go through `CLIPTextEncoder`, `SimpleIndexer` and `SimpleRanker`.
These requests have the text descriptions stored in the `text` attribute of the Documents. These texts are further encoded into vectors by `CLIPTextEncoder`. The vectors are stored in the `embedding` attribute and used to retrieve the related vectors of the video frames with the `SimpleRanker`. Last but not least, `SimpleRanker` finds the corresponding videos based on the retrieved frames. 

### Use Executors from Jina Hub

Except for `SimpleRanker`, all the other Executors used in this tutorial are available at [hub.jina.ai](https://hub.jina.ai/). We can use them off-the-shelf:

- [`VideoLoader`](https://hub.jina.ai/executor/i6gp4vwu)
- [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q)
- [`CLIPTextEncoder`](https://hub.jina.ai/executor/livtkbkg)
- [`SimpleIndexer`](https://hub.jina.ai/executor/zb38xlt4)

Note that by default `CLIPImageEncoder` encodes the `blob` of the Documents at the root level. In this example, the Document at the root level represents the video and its chunks represent video frames that the CLIP model should encode. To override this default configuration in the YAML file, we set `traversal_paths: ['c']` under the `uses_with` field. Instead of encoding the Document at the root level, the embeddings are calculated based on the `blob` of each chunk. 

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
Similar to overriding the `traversal_paths`, we need to configure the `@requests` for the Executors to ensure the requests to `/index` and `/search` endpoints can be handled as expected. The `VideoLoader` and `CLIPImageEncoder` only process requests to the `/index` endpoint. In contrast, `CLIPTextEncoder` only handles requests to the `/search` endpoint.


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

## Get the Source Code

You can find the code at [example-video-search](https://github.com/jina-ai/example-video-search). 

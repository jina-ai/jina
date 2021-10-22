# Video Search 

```{article-info}
:avatar: avatars/nan.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Nan @ Jina AI
:date: Oct. 19, 2021
```

## Search videos via Text

In this tutorial, we create a video search system that retrieves the videos based on short text descriptions of the scenes. The main challenge is to enable the user to search videos _**without**_ using any labels or text information about the videos.

<!--demo.gif-->
```{figure} ../../.github/images/tutorial-video-search.gif
:align: center
```

## Build the Flow

Given that there is no text available, we can not use the text information of the video to match the query text directly. Instead, we need figure out another way to match videos and texts. 
One way to find such matches is to use the video frames because part of the information in the videos can be captured by the frames. To be more concrete, we can find the related frames with similar semantics to the query texts and afterwards return the videos containing these frames. This requires models to encode the video frames and the query texts into the same space. In this case, the pretrained cross-modal models can help us out.

```{admonition} Use the other information of videos
:class: tip

Generally, videos contain three sources of information, namely text, image, and audio information. 
The ratio of information from different sources varies from video to video. 
In this example, only the image information is used and this assumes that the frame images are 
representative for the video and can match the query needs of the user. 
In other words, this example only works when a video contains various frames and the user's 
query needs is to search the video frames via text. 

If a video only contains texts or a video only has a single static image, 
this example won't work well. In such cases,
 the main information of the video is represented by either text or audio and therefore can 
 not be searchable with the video frames. 

Another pitfall of this tutorial is that the user might want to search with a description of 
the story, for example, `Padmé Amidala and C-3PO are taken hostage by General Grievous`. 
This information can not be described by a single frame and the query needs further understanding of 
the video. This is beyond the scope of this tutorial.
```

### Choose Executors
To encode video frames and query texts into the same space, we choose the pretrained [CLIP model](https://github.com/openai/CLIP) from OpenAI. 

```{admonition} What is CLIP?
:class: info

The CLIP model is trained to learn the visual concepts from the natural languages by using text snippet and the image pairs across the internet. In the original CLIP paper, the model is used to perform Zero Shot Learning by encoding the text labels and the images with seperated models and later calculated the similarities between the encoded vectors. 
```

In this tutorial, we use the image and the text encoding parts from CLIP to calculate the embeddings. 

```{admonition} How CLIP helps?
:class: info

Given a short text `this is a dog`, the CLIP text model can encode it into a vector. Meanwhile, the CLIP image model can encode one image of a dog and one image of a cat into the same vector space.
We can further find the distance between the text vector and the vectors of the dog image is smaller than that between the same text and an image of a cat. 
```

As for the indexer, considering this is for demonstration purpose, we choose `SimpleIndexer` as our indexer. It stores both vectors and meta-information at one shot. The search part is done by using the built-in `match` function of the `DocumentArrayMemmap`.

## Go through the Flow
Although there is only one Flow defined in this example, it handles the requests to `/index` and `/search` differently by setting the `requests` decorators for the executors. 

```{figure} ../../.github/images/tutorial-video-search.png
:align: center
```

### Index
As for the requests to the `/index` endpoint, there are three executors involved, namely `VideoLoader`, `CLIPImageEncoder` and `SimpleIndexer`. The inputs to the Flow are Documents with video URIs stored in the `uri` attributes. They are the file locations either remotely on the cloud or at your local file system. 

The `VideoLoader` extracts the frames from the video and stores them as image arrays into the `blob` attribute of the Chunks. 

The Documents after `VideoLoader` have the following format,

```{figure} ../../.github/images/tutorial-video-search-doc.jpg
:align: center
```


As the second step, `CLIPImageEncoder` calculates the `embedding` attribute for each chunk based on the CLIP model for images. The resulted vectors is 512-dimensional. 


Afterwards, the `SimpleIndexer` stores all the Documents with a memory map.  

### Query

When being posted to the `/search` endpoint, the requests go through `CLIPTextEncoder`, `SimpleIndexer` and `SimpleRanker`.
The requests have the text descriptions stored in the `text` attributes of the Documents. These texts are further encoded into vectors by `CLIPTextEncoder`. The vectors are stored in the `embedding` attribute and used to retrieve the related vectors of the video frames with the `SimpleRanker`. Last but not the least, `SimpleRanker` find out the corresponding videos based on the retrieved frames. 

### Use the executors from Jina Hub

Except the `SimpleRanker`, all the other executors used in this tutorial are available at [hub.jina.ai](https://hub.jina.ai/). We can use them off-the-shelf. 

- [`VideoLoader`](https://hub.jina.ai/executor/i6gp4vwu)
- [`CLIPImageEncoder`](https://hub.jina.ai/executor/0hnlmu3q)
- [`CLIPTextEncoder`](https://hub.jina.ai/executor/livtkbkg)
- [`SimpleIndexer`](https://hub.jina.ai/executor/zb38xlt4)

Note that by default the `CLIPImageEncoder` encodes the `blob` of the Documents at the root level. In this example, the Document at the root level represents the video and its chunks represent the video frames that the CLIP model should encode. To override this default configuration in the YAML file, we set `traversal_paths: ['c']` under the `uses_with` field. Instead of encoding the Document at the root level, the embeddings is calculated based on the `blob` of each 
chunk. 

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
Similar as overriding the `traversal_paths`, we need configurate the `@requests` for the executors to ensure the requests to `/index` and `/search` endpoints can be handled as expected. The `VideoLoader` and `CLIPImageEncoder` only process the requests to the `/index` endpoint. In contrary, the `CLIPTextEncoder` is only used to handle the requests to the `/search` endpoint.


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

## Get the Full Example Codes

You can find the codes at [example-video-search](https://github.com/jina-ai/example-video-search). 
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

## Build the Flow

Considering there is no text information available, we need find a way to match videos and texts. 
One way to find such matches is to use the video frames because the information of the videos can be represented by the frames. To be more concrete, we can find the related frames with similar semantics based on the query texts and afterward return the videos containing these frames. This requires the models to encode the video frames into the same space as the query texts. In this case, the pretrained cross-modal models can help us out.

### Choose Executors
To encode video frames and query texts into the same space, we choose the pretrained CLIP models from OpenAI. There is one model for images and one model for texts. Given a short text `this is a dog`, the CLIP text model can encode it into a vector. Meanwhile, the CLIP image model can encode one image of a dog and one image of a cat into the same vector space.
We can further find the distance between the text vector and the vectors of the dog image is smaller than that between the same text and an image of a cat. 

As for the indexer, considering this is for demonstration purpose, we choose `SimpleIndexer` as our indexer. It is a mixture of vector indexer and key-value indexer and therefore can store both vectors and meta-information at one shot.

## Go through the Flow

### Index
In the indexing part, there are three executors involved, namely `VideoLoader`, `CLIPImageEncoder` and `SimpleIndexer`. The inputs to the Flow are Documents with video URIs stored in the `uri` attributes. They are the file locations either remotely on the cloud or at your local file system. The `VideoLoader` extracts the frames from the video and stores them as image arrays into the `blob` attribute of the Chunks. The Documents after `VideoLoader` have the following format,

<!--document.png-->


As the second step, `CLIPImageEncoder` calculates the `embedding` attribute for each chunk based on the CLIP model for images. The resulted vectors is 512-dimensional. 


Afterwards, the `SimpleIndexer` stores all the Documents with a memory map.  

### Query

When being posted to the `search` endpoint, the requests go through `CLIPTextEncoder`, `SimpleIndexer` and `SimpleRanker`.
The requests have the text descriptions stored in the `text` attributes of the Documents. These texts are further encoded into vectors by `CLIPTextEncoder`. The vectors are stored in the `embedding` attribute and used to retrieve the related vectors of the video frames with the `SimpleRanker`. Last but not the least, `SimpleRanker` find out the corresponding videos based on the retrieved frames. 

### Use the executors from Jina Hub

Except the `SimpleRanker`, all the other executors used in this tutorial are available at [hub.jina.ai](https://hub.jina.ai/). We can use them off-the-shelf. 

- `CLIPImageEncoder` 
- `CLIPTextEncoder` 
- `SimpleIndexer`

Note that by default the `CLIPImageEncoder` encodes the `blob` of the Documents at the root level. In this example, the Document at the root level represents the video and its chunks represent the video frames that the CLIP model should encode. To override this default configuration in the YAML file, we set `traversal_paths: ['c']` under the `uses_with` field. Instead of encoding the Document at the root level, the embeddings is calculated based on the `blob` of each 
chunk. 

```yaml
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


```yaml
...
executors:
  - uses: jinahub://VideoLoader/v0.1
    ...
    uses_requests:  # override the @requests
      /index: 'extract'
  - uses: jinahub://CLIPImageEncoder/v0.1
    ...
    uses_requests:  # override the @requests
      /index: 'encode'
  - uses: jinahub://CLIPTextEncoder/v0.1
    ...
    uses_requests:  # override the @requests
      /search: 'encode'
...
```



## Next Steps

To further explore the power of cross-modal search, you can extend this example to enable
- Find the videos containing related audio tracks based on text descriptions
- Find the videos containing similar frames to the query image
- Find the videos containing 
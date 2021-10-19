# Video Search 

## Search videos via Text

In this tutorial, we create a video search system that retrieves the videos based on short text descriptions of the scenes. 

<!--demo.gif-->

## Build the Flow

The main goal is to enable the user to search videos with text descriptions without any labels or text information about the videos.

Considering there is no text information, we need to use the AI models  to figure out the matching relation between videos and the texts. 
Luckily, there are pretrained CLIP models to help us encode the images and texts into the same vector space. As the information of the videos can be represented by the frames, we can use the CLIP models to encode both the video frames as images and the query texts. So that the related videos can be retrieved based on the matched frames. A plus  


### Choose Encoder
To encode video frames and query texts into the same space, we choose the CLIP models from OpenAI. We will see that the pretrained CLIP models has done a pretty good job. 

Considering this is for demostration purpose, we choose `SimpleIndexer` as our indexer. It is a mixture of vector indexer and key-value indexer and therefore can store both vectors and meta-information at one shot.

## Go through the Flow

In the indexing part, we have three executors involved, namely `VideoLoader`, `CLIPImageEncoder` and `SimpleIndexer`. The inputs to the Flow are Documents with video uri stored in the `uri` attributes. They can the file locations either remotely on the cloud or in your local file system. The `VideoLoader` extracts the frames from the video and store them as image arrays into the `blob` attribute of the Chunks. The Documents after `VideoLoader` have the following format,

<!--document.png-->


As the second step, `CLIPImageEncoder` calculates the `embedding` attribute for each chunk in the Documents based on the CLIP model for images. The resulted vectors from the model is 512-dimensional. 


Afterwards, the `SimpleIndexer` stores all the Document into 

### Use the executors from Jina Hub

### Override requests configuration 

### Implement 



## Next Steps

To further explore the power of cross-modal search, you can extend this example to enable
- Find the videos containing related audio tracks based on text descriptions
- Find the videos containing similar frames to the query image
- Find the videos containing 
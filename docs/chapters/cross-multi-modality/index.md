## Multi & Cross Modality

Jina is a data type-agnostic framework. It basically can work with any kind of data. 

Jina does not only offer the possibility to work with any data, but also allows you to run cross- and multi-modal search flows. 
To better understand what this implies we first need to understand the concept of modality. 

One may think that different modalities correspond to different kinds of data (images and text in this case).
However, this is not accurate. For example, one can do cross-modal search by searching images from different points of view, 
or searching for matching titles for given paragraph text.
Therefore, one can consider that a modality is related to a given data distribution from which input may come. 

For this reason, and to have first-class support for cross and multi-modal search, Jina offers modality as an attribute in its Document primitive type.
Now that we are agreed on the concept of modality, we can describe cross-modal and multi-modal search.
 
 - Cross-modal search can be defined as a set of retrieval applications that try to effectively find relevant documents of modality A by querying with documents from modality B.
 - Multi-modal search can be defined as a set of retrieval applications that try to effectively project documents of different modalities into a
 common embedding space, and find relevant documents with respect to the fusion of multiple modalities
 
The main difference between these two search modes is that for cross-modal, there is a direct mapping between a single document or chunk and a
vector in embedding space, while for MultiModal this does not hold true, since 2 or more documents might be combined into a single vector.
 
This unlocks a lot of powerful patterns and makes Jina fully flexible and agnostic to what can be searched.
 
 - It allows to look for images by giving corresponding caption descriptions (https://github.com/jina-ai/examples/tree/master/cross-modal-search)
 - It allows to merge visual and textual information in a multi-modal way to look for images with transformation descriptions ( - It allows to look for images by giving corresponding caption descriptions (https://github.com/jina-ai/examples/tree/master/multi-modal-search-tirg)
 
### Cross modal search

Supporting cross-modal search in Jina is very easy. One just needs to properly set the modality field of the input documents
and design the Flow in such a way that the queries target the desired embedding space.

### Multi modal search

In order to support multi-modal search and to make it easy to build such applications, Jina provides three new concepts.
 
 - `MultiModalDocument`: `MultiModalDocument` is a document composed by more than one chunk with different modalities. It makes it easy
 for the client and for the multimodal drivers to build and work with these constructions.
 - `MultiModalEncoder`: `MultiModalEncoder` is a new family of Executors, derived from the Encoders, that encodes data coming from more than 
 one modality into a single embedding vector.
 - `MultiModalDriver`: `MultiModalDriver` is a new Driver designed to extract the expected content from every chunk inside MultiModalDocuments
 and to provide it to the executor.

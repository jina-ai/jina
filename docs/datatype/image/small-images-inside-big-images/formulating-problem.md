## Understanding And Formulating the Problem
As we want to find small images inside big images, simply encoding both the indexed images and the query image and 
matching will not work. Imagine that you have the following big image :

```{figure} cat-bird.jpg
:align: center
:width: 60%
```

It contains a scene with a cat in the background, a bird and a few other items in the scene.

Now let's suppose that the query image is a simple bird:

```{figure} bird.jpg
:align: center
:width: 10%
```

Encoding the query image will generate embeddings that effectively represent it. However, it's not easy to build an 
encoder that effectively represents the big image, since it contains a complex scene with different objects. 
The embeddings will not be representative enough and therefore we need to think about a better approach.

Can you think of another solution ?

````{admonition} Hint
:class: hint
Encoding a complex image is not easy, but what if we can encode objects inside it ?
Imagine that we can identify these objects inside the big image like so:

```{figure} cat-bird-detections.jpg
:align: center
:width: 60%
```
````

Right, identifying objects inside the big image and then encoding each one of them will result in better, more 
representative embeddings.
Right now, we should ask 2 questions:
1. How can we identify objects ?
2. How can we retrieve the big image if we match the query against identified objects ?


The first question is easy. And the response is simply [object detection](https://en.wikipedia.org/wiki/Object_detection).
There are many models that can perform object detection and in this tutorial, we will be using [yolov5](https://github.com/ultralytics/yolov5).
Detected objects can be easily represented as chunks of the original indexed documents.

```{admonition} See Also
:class: seealso
If you're not familiar with `chunks` in jina, check this {ref}`section <recursive-nested-document>`
```

The second question can be a bit complex. Actually, we will match query documents against chunks of the original 
documents but we need to return the original documents (the big images). We can solve this problem by relying on a 
ranker executor, which roughly does the following:
1. Retrieve the parent document IDs from the matched chunks along with their scores
2. For each parent ID, aggregate the scores of that parent
3. Replace the matches by the parent documents instead of children documents (aka chunks).
4. Sort the new matches by their aggregated scores.

Cool, seems like a complex logic, but no worries, we will build our ranker executor later step by step. However, note 
that since the ranker is not a storage executor, it's not capable of retrieving the parent documents from chunks. 
Instead, we can create empty documents that only contain the IDs. This implies that in a later step, we need to 
retrieve those documents by IDs.

Now let's try to imagine and design our Flows given what we've discussed so far:


Index Flow:

```{figure} index_flow_brainstorming.svg
:align: center
```

Query Flow:

```{figure} query_flow_brainstorming.svg
:align: center
```

Oh, because we use the ranker, we will need something to help us retrieve original parent documents by IDs.
Well that can be any storage executor. Actually [Jina Hub](https://hub.jina.ai) includes many storage executors but in this 
tutorial, we will build our own storage executor. Since this executor should store parent documents, we will call it 
the `root_indexer`. Also, since we need it in the query Flow, we also have to add it to the index Flow. One more note, 
this `root_indexer` will index documents as they are, so it makes sense to put it in parallel to the other processing 
steps (segmenting, encoding,...).

Now, the technology behind this executor will be [LMDB](https://en.wikipedia.org/wiki/Lightning_Memory-Mapped_Database).

```{admonition} See Also
:class: seealso
Jina natively supports complex toplogies of Flow where you can put executors in parallel. Checkout 
{ref}`this section <flow-topology>` to learn more.
```

Cool, but what about the other indexer ?

Well, it should support matching and indexing chunks of images after they are 
segmented. Therefore, it needs to support vector search along with indexing. The [Jina Hub](https://hub.jina.ai) already 
includes such indexers (for example, `SimpleIndexer`), however, we will create our own version of simple indexer. And 
by the way, it will be convenient to rename this indexer to `chunks_indexer`.

Alright, before seeing the final architecture, let's agree on names for our executors:
* `chunks_indexer`: `SimpleIndexer`
* `root_indexer`: `LMDBStorage` (well because we use LMDB)
* `encoder`: `CLIPImageEncoder` (yes we will be using the `CLIP` model to encode images)
* `segmenter`: `YoloV5Segmenter`. Actually we could name `object-detector` but `segmenter` is a term that aligns 
better with Jina's terminology
* `ranker`: `SimpleRanker` (trust me it's going to be simple)

Finally, here is what our Flows will look like.
Index Flow:

```{figure} index_flow.svg
:align: center
```

Query Flow:

```{figure} query_flow.svg
:align: center
```


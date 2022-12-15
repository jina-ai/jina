## Building Executors
In this section, we will start developing the necessary executors, for both query and index flows.

### **CLIPImageEncoder**
This encoder encodes an image into embeddings using the CLIP model. 
We want an executor that loads the CLIP model and encodes it during the query and index flows. 

Our executor should:
* support both **GPU** and **CPU**: That's why we will provision the `device` parameter and use it when encoding.
* be able to process documents in batches in order to use our resources effectively: To do so, we will use the 
parameter `batch_size`
* be able to encode the full image during the query flow and encode only chunks during the index flow: This can be 
achieved with `traversal_paths` and method `DocumentArray.batch`.

```python
from typing import Optional, Tuple

import torch
from jina import DocumentArray, Executor, requests
from jina.logging.logger import JinaLogger
from transformers import CLIPFeatureExtractor, CLIPModel


class CLIPImageEncoder(Executor):
    """Encode image into embeddings using the CLIP model."""

    def __init__(
        self,
        pretrained_model_name_or_path: str = "openai/clip-vit-base-patch32",
        device: str = "cpu",
        batch_size: int = 32,
        traversal_paths: Tuple = ("r",),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size
        self.traversal_paths = traversal_paths
        self.pretrained_model_name_or_path = pretrained_model_name_or_path

        self.device = device
        self.preprocessor = CLIPFeatureExtractor.from_pretrained(
            pretrained_model_name_or_path
        )
        self.model = CLIPModel.from_pretrained(self.pretrained_model_name_or_path)
        self.model.to(self.device).eval()

    @requests
    def encode(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
        if docs is None:
            return

        traversal_paths = parameters.get("traversal_paths", self.traversal_paths)
        batch_size = parameters.get("batch_size", self.batch_size)
        document_batches_generator = docs.batch(
            traversal_paths=traversal_paths,
            batch_size=batch_size,
            require_attr="blob",
        )

        with torch.inference_mode():
            for batch_docs in document_batches_generator:
                blob_batch = [d.blob for d in batch_docs]
                tensor = self._generate_input_features(blob_batch)


                embeddings = self.model.get_image_features(**tensor)
                embeddings = embeddings.cpu().numpy()

                for doc, embed in zip(batch_docs, embeddings):
                    doc.embedding = embed

    def _generate_input_features(self, images):
        input_tokens = self.preprocessor(
            images=images,
            return_tensors="pt",
        )
        input_tokens = {
            k: v.to(torch.device(self.device)) for k, v in input_tokens.items()
        }
        return input_tokens
```

### **YoloV5Segmenter**
Since we want to retrieve small images in bigger images, the technique that we will heavily rely on is segmenting. 
Basically, we want to do object detection on the indexed images. This will generate bounding boxes around objects 
detected inside the images. The detected objects will be extracted and added as chunks to the original documents.
By the way, guess what is the state-of-the-art object detection model ?

Right, we will use YoloV5.


Our **YoloV5Segmenter** should be able to load the `ultralytics/yolov5` model from Torch hub, otherwise, load a custom 
model. To achieve this, the executor accepts parameter `model_name_or_path` which will be used when loading. We will 
implement the method `load` which checks if the model exists in the the Torch Hub, otherwise, loads it as a custom model.

For our use case, we will just rely on `yolov5s` (small version of `yolov5`). Of course, for better quality, you can 
choose a more complicated model or your custom model.

Furthermore, we want **YoloV5Segmenter** to support both **GPU** and **CPU** and it should be able to process in 
batches. Again, this is as simple as adding parameters `device` and `batch_size` and using them during segmenting.

To perform segmenting, we will implement method `_segment_docs` which performs the following steps:
1. For each batch (a batch consists of several images), use the model to get predictions for each image
2. Each prediction of an image can contain several detections (because yolov5 will extract as much bounding boxes as 
possible, along with their confidence scores). We will filter out detections whose scores are below the `confidence_threshold` to keep good quality.

Each detection is actually 2 points -top left (x1, y1) and bottom right (x2, y2)- a confidence score and a class. 
We will not use the class of the detection, but it can be useful in other search applications.

3. With the detections that we have, we create crops (using the 2 points returned). Finally, we add these crops to 
image documents as chunks.


```python
from typing import Dict, Iterable, Optional

import torch
from jina import Document, DocumentArray, Executor, requests
from jina_commons.batching import get_docs_batch_generator


class YoloV5Segmenter(Executor):

    def __init__(
        self,
        model_name_or_path: str = 'yolov5s',
        confidence_threshold: float = 0.3,
        batch_size: int = 32,
        device: str = 'cpu',
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.model_name_or_path = model_name_or_path
        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size

        if device != 'cpu' and not device.startswith('cuda'):
            self.logger.error('Torch device not supported. Must be cpu or cuda!')
            raise RuntimeError('Torch device not supported. Must be cpu or cuda!')
        if device == 'cuda' and not torch.cuda.is_available():
            self.logger.warning(
                'You tried to use GPU but torch did not detect your'
                'GPU correctly. Defaulting to CPU. Check your CUDA installation!'
            )
            device = 'cpu'
        self.device = torch.device(device)
        self.model = self._load(self.model_name_or_path)

    @requests
    def segment(
        self, docs: Optional[DocumentArray] = None, parameters: Dict = {}, **kwargs
    ):

        if docs:
            document_batches_generator = get_docs_batch_generator(
                docs,
                traversal_path=['r'],
                batch_size=parameters.get('batch_size', self.batch_size),
                needs_attr='blob',
            )
            self._segment_docs(document_batches_generator, parameters=parameters)

    def _segment_docs(self, document_batches_generator: Iterable, parameters: Dict):
        with torch.no_grad():
            for document_batch in document_batches_generator:
                images = [d.blob for d in document_batch]
                predictions = self.model(
                    images,
                    size=640,
                    augment=False,
                ).pred

                for doc, prediction in zip(document_batch, predictions):
                    for det in prediction:
                        x1, y1, x2, y2, conf, cls = det
                        if conf < parameters.get(
                            'confidence_threshold', self.confidence_threshold
                        ):
                            continue
                        crop = doc.blob[int(y1) : int(y2), int(x1) : int(x2), :]
                        doc.chunks.append(Document(blob=crop))

    def _load(self, model_name_or_path):
        if model_name_or_path in torch.hub.list('ultralytics/yolov5'):
            return torch.hub.load(
                'ultralytics/yolov5', model_name_or_path, device=self.device
            )
        else:
            return torch.hub.load(
                'ultralytics/yolov5', 'custom', model_name_or_path, device=self.device
            )
```

**Indexers**

After developing the encoder, we will need 2 kinds of indexers: 
1. SimpleIndexer: This indexer will take care of storing chunks of images. It also should support vector similarity 
search which is important to match small query images against segments of original images.

2. LMDBStorage: LMDB is a simple memory-mapped transactional key-value store. It is convenient for this example 
because we can use it to store the original images (so that we can retrieve them later). We will use it to create 
LMDBStorage which offers 2 functionalities: indexing documents and retrieving documents by ID.


### **SimpleIndexer**

To implement SimpleIndexer, we can leverage Jina's `DocumentArrayMemmap`. You can read about this data type 
[here](https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/).

Our indexer will create an instance of `DocumentArrayMemmap` when it's initialized. We want to store indexed documents 
inside the workspace folder that's why we pass the `workspace` attribute of the executor to `DocumentArrayMemmap`.

To index, we implement the method `index` which is bound to the index flow. It's as simple as extending the received 
docs to `DocumentArrayMemmap` instance.

On the other hand, for search, we implement the method `search`. We bind it to the query flow using the decorator 
`@requests(on='/search')`.

In jina, searching for query documents can be done by adding the results to the `matches` attribute of each query 
document. Since docs is a `DocumentArray` we can use method `match` to match query against the indexed documents.
Read more about `match` [here](https://docs.jina.ai/fundamentals/document/documentarray-api/#matching-documentarray-to-another).
There's another detail here. We already indexed documents before search, but we need to match query documents against 
chunks of the indexed images. Luckily, `DocumentArray.match` allows us to specify the traversal paths of 
the right-hand-side parameter with parameter `traversal_rdarray`. Since we want to match the left side docs (query) 
against the chunks of the right side docs (indexed docs), we can specify that `traversal_rdarray=['c']`.

```python
from typing import Dict, Optional

from jina import DocumentArray, Executor, requests
from jina.types.arrays.memmap import DocumentArrayMemmap


class SimpleIndexer(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._storage = DocumentArrayMemmap(
            self.workspace, key_length=kwargs.get('key_length', 64)
        )

    @requests(on='/index')
    def index(
        self,
        docs: Optional['DocumentArray'] = None,
        **kwargs,
    ):
        if docs:
            self._storage.extend(docs)

    @requests(on='/search')
    def search(
        self,
        docs: Optional['DocumentArray'] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ):
        if not docs:
            return

        docs.match(self._storage, traversal_rdarray=['c'])

```

### **LMDBStorage**

In order to implement the LMDBStorage, we need the following parts:

**I. Handler**

This will be a context manager that we will use when we access our LMDB database. We will create it as a standalone 
class.


**II. LMDBStorage constructor**

The constructor should initialize a few attributes:
* the `map_size` of the database
* the `default_traversal_paths`. Actually we need traversal paths because we will not be traversing documents in 
the same way during index and query flows. During index, we want to store the root documents. However, during query,  
we need to get the matches of documents by ID.
* the index file: again, to keep things clean, we will store the index file inside the workspace folder. Therefore we 
can use the `workspace` attribute.


**III. `LMDBStorage.index`**

In order to index documents, we first start a transaction (so that our Storage executor is ACID-compliant). Then, we 
traverse them according to the `traversal_paths` (will be root in the index Flow). Finally, each document is serialized 
to string and then added to the database (the key is the document ID)


**IV. `LMDBStorage.search`**

Unlike search in the SimpleIndexer, we only wish to get the matched Documents by ID and return them. Actually, the 
matched documents will be empty and will only contain the IDs. The goal is to return full matched documents using IDs.
To accomplish this, again, we start a transaction, traverse the matched documents, get each matched document by ID and 
use the results to fill our documents.

```python
import os
from typing import Dict, List

import lmdb
from jina import Document, DocumentArray, Executor, requests


class _LMDBHandler:
    def __init__(self, file, map_size):
        # see https://lmdb.readthedocs.io/en/release/#environment-class for usage
        self.file = file
        self.map_size = map_size

    @property
    def env(self):
        return self._env

    def __enter__(self):
        self._env = lmdb.Environment(
            self.file,
            map_size=self.map_size,
            subdir=False,
            readonly=False,
            metasync=True,
            sync=True,
            map_async=False,
            mode=493,
            create=True,
            readahead=True,
            writemap=False,
            meminit=True,
            max_readers=126,
            max_dbs=0,  # means only one db
            max_spare_txns=1,
            lock=True,
        )
        return self._env

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_env'):
            self._env.close()


class LMDBStorage(Executor):
    def __init__(
        self,
        map_size: int = 1048576000,  # in bytes, 1000 MB
        default_traversal_paths: List[str] = ['r'],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.map_size = map_size
        self.default_traversal_paths = default_traversal_paths
        self.file = os.path.join(self.workspace, 'db.lmdb')
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

    def _handler(self):
        return _LMDBHandler(self.file, self.map_size)

    @requests(on='/index')
    def index(self, docs: DocumentArray, parameters: Dict, **kwargs):
        traversal_paths = parameters.get(
            'traversal_paths', self.default_traversal_paths
        )
        if docs is None:
            return
        with self._handler() as env:
            with env.begin(write=True) as transaction:
                for d in docs.traverse_flat(traversal_paths):
                    transaction.put(d.id.encode(), d.SerializeToString())

    @requests(on='/search')
    def search(self, docs: DocumentArray, parameters: Dict, **kwargs):
        traversal_paths = parameters.get(
            'traversal_paths', self.default_traversal_paths
        )
        if docs is None:
            return
        docs_to_get = docs.traverse_flat(traversal_paths)
        with self._handler() as env:
            with env.begin(write=True) as transaction:
                for i, d in enumerate(docs_to_get):
                    id = d.id
                    serialized_doc = Document(transaction.get(d.id.encode()))
                    d.update(serialized_doc)
                    d.id = id

```

### **SimpleRanker**

You might think why do we need a ranker at all ?

Actually, a ranker is needed because we will be matching small query images against chunks of parent documents. But how 
can we get back to parent documents (aka full images) given the chunks ? And what if 2 chunks belonging to the same 
parent are matched ?
We can solve this by aggregating the similarity scores of chunks that belong to the same parent (using an aggregation 
method, in our case, will be the `min` value).
So, for each query document, we perform the following:

1. We create an empty collection of parent scores. This collection will store, for each parent, a list of scores of its 
chunk documents.
2. For each match, since it's a chunk document, we can retrieve its `parent_id`. And it's also a match 
document so we get its match score and add that value to the parent scores collection.
3. After processing all matches, we need to aggregate the scores of each parent using the `min` metric.
4. Finally, using the aggregated score values of parents, we can create a new list of matches (this time consisting 
of parents, not chunks). We also need to sort the matches list by aggregated scores.

When query documents exit the SimpleRanker, they now have matches consisting of parent documents. However, parent 
documents just have IDs. That's why, during the previous steps, we created LMDBStorage: to actually 
retrieve parent documents by IDs and fill them with data.

```python
from collections import defaultdict
from typing import Dict, Iterable, Optional

from jina import Document, DocumentArray, Executor, requests


class SimpleRanker(Executor):
    def __init__(
        self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metric = 'cosine'

    @requests(on='/search')
    def rank(
        self, docs: Optional[DocumentArray] = None, parameters: Dict = {}, **kwargs
    ):
        if docs is None:
            return

        for doc in docs:
            parents_scores = defaultdict(list)
            for m in DocumentArray([doc]).traverse_flat(['m']):
                parents_scores[m.parent_id].append(m.scores[self.metric].value)

            # Aggregate match scores for parent document and
            # create doc's match based on parent document of matched chunks
            new_matches = []
            for match_parent_id, scores in parents_scores.items():
                score = min(scores)

                new_matches.append(
                    Document(id=match_parent_id, scores={self.metric: score})
                )

            # Sort the matches
            doc.matches = new_matches
            doc.matches.sort(key=lambda d: d.scores[self.metric].value)

```


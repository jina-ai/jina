# Search Image from Text via CLIP model

In this tutorial, we will create an image search system that retrieves images based on short text descriptions as query.

The interest behind this is that in regular search, image description or meta data describing the content of the image needs to be indexed first before retrieving the images via text query. This can be expensive because you need a person to write that description and also information about image content is not always available.

We need to look for another solution! What if we can directly compare text with images?  

To do so, we need to figure out a way to match images and text. One way is finding related images with similar semantics to the query text. This requires us to represent both images and query text in the same embedding space to be able to do the matching. In this case, pre-trained cross-modal models can help us out.

For example when we write the word "dog" in query we want to be able to retrieve pictures with a dog solely by using the embeddings similarity.

```{tip}
The full source code of this tutorial is available in this [Google Colab notebook](https://colab.research.google.com/github/jina-ai/workshops/blob/docs-add-text-to-image-notebook/text2image/Image_Search_via_Text.ipynb)
```

Now that we understand the problem and we have an idea on how to fix it, let's try to imagine what the solution would look like: 

1. We have a bunch of images with no text description about the content.
2. We use a model to create an embedding that represents those images. 
3. Now we will index and save our embeddings which we will call Documents inside a workspace folder. 

This is what we call the index Flow.  

```{figure} index_flow_text2image.svg
:align: center
```

Now to search for an image using text we do the following 

1. We embed the query text into the same embedding space as the image.
2. We compute similarity between the query embedding and previously saved embeddings. 
3. We return the best results.

This is our query Flow. 

```{figure} query_flow_text2image.svg
:align: center
```

If we had to build this from scratch, it would take a long time to build these Flows. Luckily we can leverage Jina's tools such as Executors, Documents and Flows 
and build such a system easily.
## Pre-requisites

Before we begin building our Flow we need to do a few things. 

* Install the following dependencies.

```shell
pip install Pillow jina torch==1.9.0 torchvision==0.10.0 transformers==4.9.1 matplotlib jina-commons@git+https://github.com/jina-ai/jina-commons.git#egg=jina-commons
```

* Download [the dataset](https://open-images.s3.eu-central-1.amazonaws.com/data.zip) and unzip it.

You can use the link or the following commands:
```shell
wget https://open-images.s3.eu-central-1.amazonaws.com/data.zip
unzip data.zip
```

You should find two folders after unzipping:
* images: this folder contains the images that we will index.
* query: this folder contains small images that we will use as search queries.

## Building Executors
In this section, we will start developing the necessary Executors, for both query and index Flows.

To encode images and query text into the same space, we choose the pre-trained [CLIP model](https://github.com/openai/CLIP) from OpenAI. 

```{admonition} What is CLIP?
:class: info

The CLIP model is trained to learn visual concepts from natural languages. This is done using text snippets and image pairs across the internet. In the original CLIP paper, the model performs Zero Shot Learning by encoding text labels and images with separate models. Later the similarities between the encoded vectors are calculated. 
```

In this tutorial, we use the image and the text encoding parts from CLIP to calculate the embeddings. 

```{admonition} How does CLIP help?
:class: info

Given a short text `this is a dog`, the CLIP text model can encode it into a vector. Meanwhile, the CLIP image model can encode one image of a dog and one image of a cat into the same vector space.
We can further find the distance between the text vector and the vectors of the dog image is smaller than that between the same text and an image of a cat. 
```

### **CLIPImageEncoder**
This encoder encodes an image into embeddings using the CLIP model. 
We want an Executor that loads the CLIP model and encodes images during the index Flow. 

Our Executor should:
* Support both **GPU** and **CPU**: That's why we will provision the `device` parameter and use it when encoding.
* Be able to process Documents in batches in order to use our resources effectively: To do so, we will use the 
parameter `batch_size`

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
        base_feature_extractor: Optional[str] = None,
        use_default_preprocessing: bool = True,
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
        self.use_default_preprocessing = use_default_preprocessing
        self.base_feature_extractor = (
            base_feature_extractor or pretrained_model_name_or_path
        )

        self.device = device
        self.preprocessor = CLIPFeatureExtractor.from_pretrained(
            self.base_feature_extractor
        )
        self.model = CLIPModel.from_pretrained(self.pretrained_model_name_or_path)
        self.model.to(self.device).eval()

    @requests
    def encode(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
      
        if docs is None:
            return

        traversal_paths = parameters.get("traversal_paths", self.traversal_paths)
        batch_size = parameters.get("batch_size", self.batch_size)
        document_batches_generator =  docs.traverse_flat(parameters.get('traversal_paths', self.traversal_paths)).batch(
            batch_size=batch_size
        )

        with torch.inference_mode():
            for batch_docs in document_batches_generator:
                blob_batch = [d.blob for d in batch_docs]
                if self.use_default_preprocessing:
                    tensor = self._generate_input_features(blob_batch)
                else:
                    tensor = {
                        "pixel_values": torch.tensor(
                            blob_batch, dtype=torch.float32, device=self.device
                        )
                    }

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
### **CLIPTextEncoder**
This encoder encodes a text into embeddings using the CLIP model. 
We want an Executor that loads the CLIP model and encodes it during the query Flow. 

Our Executor should:
* Support both **GPU** and **CPU**: That's why we will provision the `device` parameter and use it when encoding.
* Be able to process Documents in batches in order to use our resources effectively: To do so, we will use the 
parameter `batch_size`

```python
from transformers import  CLIPTokenizer

class CLIPTextEncoder(Executor):
    """Encode text into embeddings using the CLIP model."""

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'openai/clip-vit-base-patch32',
        base_tokenizer_model: Optional[str] = None,
        max_length: int = 77,
        device: str = 'cpu',
        traversal_paths: Sequence[str] = ['r'],
        batch_size: int = 32,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.traversal_paths = traversal_paths
        self.batch_size = batch_size
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.base_tokenizer_model = (
            base_tokenizer_model or pretrained_model_name_or_path
        )
        self.max_length = max_length

        self.device = device
        self.tokenizer = CLIPTokenizer.from_pretrained(self.base_tokenizer_model)
        self.model = CLIPModel.from_pretrained(self.pretrained_model_name_or_path)
        self.model.eval().to(device)

    @requests
    def encode(self, docs: Optional[DocumentArray], parameters: Dict, **kwargs):
        if docs is None:
            return

        for docs_batch in docs.traverse_flat(parameters.get('traversal_paths', self.traversal_paths)).batch(
            batch_size=parameters.get('batch_size', self.batch_size)
        ):
            text_batch = docs_batch.get_attributes('text')

            with torch.inference_mode():
                input_tokens = self._generate_input_tokens(text_batch)
                embeddings = self.model.get_text_features(**input_tokens).cpu().numpy()
                for doc, embedding in zip(docs_batch, embeddings):
                    doc.embedding = embedding

    def _generate_input_tokens(self, texts: Sequence[str]):

        input_tokens = self.tokenizer(
            texts,
            max_length=self.max_length,
            padding='longest',
            truncation=True,
            return_tensors='pt',
        )
        input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}
        return input_tokens
```

### **SimpleIndexer**
To implement SimpleIndexer, we can leverage Jina's `DocumentArrayMemmap`. You can read about this data type 
[here](https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/).

Our indexer will create an instance of `DocumentArrayMemmap` when it's initialized. We want to store indexed Documents 
inside the workspace folder that's why we pass the `workspace` attribute of the Executor to `DocumentArrayMemmap`.

To index, we implement the method `index` which has `/index` as the endpoint invoked during the index Flow. It's as simple as extending the received 
docs to `DocumentArrayMemmap` instance.

On the other hand, for search, we implement the method `search`. We bind it to the query Flow using the [decorator](https://book.pythontips.com/en/latest/decorators.html) 
`@requests(on='/search')`.
In Jina, searching for query Documents can be done by adding the results to the `matches` attribute of each query 
document. Since docs is a `DocumentArray` we can use method `match` to match query against the indexed Documents.
Read more about `match` [here](https://docs.jina.ai/fundamentals/document/documentarray-api/#matching-documentarray-to-another).


```python
from typing import Dict, Optional

from jina import DocumentArray, Executor, requests
from jina.types.arrays.memmap import DocumentArrayMemmap

class SimpleIndexer(Executor):
    """
    A simple indexer that stores all the Document data together,
    in a DocumentArrayMemmap object
    To be used as a unified indexer, combining both indexing and searching
    """

    def __init__(
        self,
        match_args: Optional[Dict] = None,
        **kwargs,
    ):
        """
        Initializer function for the simple indexer
        :param match_args: the arguments to `DocumentArray`'s match function
        """
        super().__init__(**kwargs)

        self._match_args = match_args or {}
        self._storage = DocumentArrayMemmap(
            self.workspace, key_length=kwargs.get('key_length', 64)
        )

    @requests(on='/index')
    def index(
        self,
        docs: Optional['DocumentArray'] = None,
        **kwargs,
    ):
        """All Documents to the DocumentArray
        :param docs: the docs to add
        """
        if docs:
            self._storage.extend(docs)

    @requests(on='/search')
    def search(
        self,
        docs: Optional['DocumentArray'] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ):
        """Perform a vector similarity search and retrieve the full Document match
        :param docs: the Documents to search with
        :param parameters: the runtime arguments to `DocumentArray`'s match
        function. They overwrite the original match_args arguments.
        """
        if not docs:
            return
        match_args = deepcopy(self._match_args)
        if parameters:
            match_args.update(parameters)

        match_args = SimpleIndexer._filter_parameters(docs, match_args)

        docs.match(self._storage, **match_args)

    @staticmethod
    def _filter_parameters(docs, match_args):
        # get only those arguments that exist in .match
        args = set(inspect.getfullargspec(docs.match).args)
        args.discard('self')
        match_args = {k: v for k, v in match_args.items() if k in args}
        return match_args
```

## Building Flows
### Indexing
Now, after creating Executors, it's time to use them in order to build an index Flow and index our data.

#### Building the index Flow
We create a Flow object and add Executors one after the other with the right parameters: 

1. CLIPImageEncoder: We specify the device. 
2. SimpleIndexer: We need to specify the workspace parameter.

```python
from jina import Flow
flow_index = Flow() \
    .add(uses=CLIPImageEncoder, name="encoder", uses_with={"device":device}) \
    .add(uses=SimpleIndexer, name="indexer", workspace='workspace')
flow_index.plot()
```

```{figure} index_flow_text2image.svg
:align: center
```

Now it's time to index the dataset that we have downloaded. Actually, we will index images inside the `images` folder.
This helper function will convert the image files into Documents, create a generator and yields Documents:

```python
import glob
from jina import Document

def input_docs(data_path):
    for fn in glob.glob(os.path.join(data_path, '*')):
        doc = Document(uri=fn, tags={'filename': fn})
        doc.load_uri_to_image_blob()
        yield doc 
```

The final step in this section is to send the input Documents to the index Flow. Note that indexing can take a while:

```python
with flow_index:
    flow_index.post(on='/index',inputs=input_docs("/content/images"), request_size=1)
```


```text
Flow@3084[I]:🎉 Flow is ready to use!
🔗 Protocol: 		GRPC
🏠 Local access:	0.0.0.0:33367
🔒 Private network:	172.28.0.2:33367
🌐 Public address:	34.125.186.176:33367
```

### Searching
Now, let's build the search Flow and use it to search with sample query images.

Our Flow contains the following Executors:

1. CLIPTextEncoder: We specify the device.
2. SimpleIndexer: We need to specify the workspace parameter.

```python
flow_search = Flow() \
    .add(uses=CLIPTextEncoder, name="encoder", uses_with={"device":device}) \
    .add(uses=SimpleIndexer,name="indexer",workspace="workspace")
flow_search.plot()
```

Query Flow:

```{figure} query_flow_text2image.svg
:align: center
```

We create a helper function to plot our images: 

```python 
import matplotlib.pyplot as plt

def show_docs(docs):
  for doc in docs:
      plt.imshow(doc.blob)
      plt.show()
```
and one last function to show us the top three matches to our text query: 

```python 
def plot_search_results(resp: Request):
    for doc in resp.docs:
        print(f'Query text: {doc.text}')
        print(f'Matches:')
        print('-'*10)
        show_docs(doc.matches[:3])
```        

Now we input some text queries which we transform into Documents and here are the results: 

```python
with flow_search:
    resp = flow_search.post(on='/search',inputs=DocumentArray([
                    Document(text='dog'),
                    Document(text='cat'),
                    Document(text='kids on their bikes'),
                ]),on_done=plot_search_results)
```

Sample results: 

```text
Query: Dog
Results:
```
```{figure} dog1.png
:align: center
```
```{figure} dog2.png
:align: center
```
```{figure} dog3.png
:align: center
```

```text
Query: Cat
Results:
```

```{figure} cat1.png
:align: center
```
```{figure} cat2.png
:align: center
```
```{figure} cat3.png
:align: center
```

```text
Query: Kids riding bikes
Results:
```
```{figure} bike1.png
:align: center
```
```{figure} bike2.png
:align: center
```
```{figure} bike3.png
:align: center
```

Congratulations! You have built a text-to-image search engine. You can check the full source code [here](https://colab.research.google.com/github/jina-ai/workshops/blob/docs-add-text-to-image-notebook/text2image/Image_Search_via_Text.ipynb) and experiment with your own text queries.
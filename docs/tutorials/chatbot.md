# Question-Answering Chatbot via Transformer

```{article-info}
:avatar: avatars/susana.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Susana @ Jina AI
:date: June 15, 2021
```

We will use the {ref}`hello world chatbot <chatbot-helloworld>` for this tutorial. You can find the complete
code [here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot) and we will go step by step.

At the end of this tutorial, you will have your own chatbot. You will use text as an input and get a text result as
output. For this example, we will use a [covid dataset](https://www.kaggle.com/xhlulu/covidqa). You will understand how
every part of this example works and how you can create new apps with different datasets on your own.

## Define data and work directories

We can start by creating an empty folder, I'll call mine `tutorial` and that's the name you'll see through the tutorial
but feel free to use whatever you wish.

We will display our results in our browser, so download the static folder from
[here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot/static), and paste it into your tutorial
folder. This is only the CSS and HTML files to render our results. We will use a dataset in a `.csv` format. We'll use
the [COVID](https://www.kaggle.com/xhlulu/covidqa) dataset from Kaggle.

Download it under your `tutorial` directory:

```shell
wget https://static.jina.ai/chatbot/dataset.csv
```

## Create Documents from a csv file

To create a Document in Jina, we do it like this:

``` python
doc = Document(content='hello, world!')
```

In our case, the content of our Document needs to be the dataset we want to use:

``` python
from jina.types.document.generators import from_csv

with open('dataset.csv') as fp:
    docs = from_csv(fp, field_resolver={'question': 'text'})
```

So what happened there? We created a generator of Documents `docs`, and we
used [from_csv](https://docs.jina.ai/api/jina.types.document.generators/#jina.types.document.generators.from_csv) to
load our dataset. We use `field_resolver` to map the text from our dataset to the Document attributes.

Finally, we can combine the 2 previous steps (loading the dataset into Documents and starting the context) and index
like this:

``` python
from jina.types.document.generators import from_csv

with flow, open('dataset.csv') as fp:
    flow.index(from_csv(fp, field_resolver={'question': 'text'}))
```

```{admonition} See Also
:class: seealso
[from_csv](https://docs.jina.ai/api/jina.types.document.generators/#jina.types.document.generators.from_csv) is a 
function that belongs to the 
[jina.types.document.generators module](https://docs.jina.ai/api/jina.types.document.generators/).
Feel free to check it to find more generators.
```

````{admonition} Important
:class: important
`flow.index` will send the data to the `/index` endpoint. However, both of the added Executors do not have an `/index` 
endpoint. In fact, `MyTransformer` and `MyIndexer` only expose endpoints `/foo` and `/bar` respectively:
```{code-block} python
---
emphasize-lines: 2, 7
---
class MyTransformer(Executor):
    @requests(on='/foo')
    def foo(self, **kwargs):
        print(f'foo is doing cool stuff: {kwargs}')

class MyIndexer(Executor):
    @requests(on='/bar')
    def bar(self, **kwargs):
        print(f'bar is doing cool stuff: {kwargs}')
```
This simply means that no endpoint will be triggered by `flow.index`. Besides, our Executors are dummy and still do not 
have logic to index data. Later, we will modify Executors so that calling `flow.index` does indeed store the dataset.
````

## Create Flow

Let's put the Executors and the Flow together and re-organize our code a little bit. First, we should import everything
we need:

``` python
import os
import webbrowser
from pathlib import Path
from jina import Flow, Executor, requests
from jina.logging.predefined import default_logger
from jina.types.document.generators import from_csv
```

Then we should have our `main` and a `tutorial` function that contains all the code that we've done so far.
`tutorial` accepts one parameter that we'll need later:
`port_expose` (the port used to expose our Flow)

``` python
def tutorial(port_expose):
    class MyTransformer(Executor):
        @requests(on='/foo')
        def foo(self, **kwargs):
            print(f'foo is doing cool stuff: {kwargs}')

    class MyIndexer(Executor):
        @requests(on='/bar')
        def bar(self, **kwargs):
            print(f'bar is doing cool stuff: {kwargs}')

    flow = (
        Flow()
        .add(name='MyTransformer', uses=MyTransformer)
        .add(name='MyIndexer', uses=MyIndexer)
    )
    with flow, open('dataset.csv') as fp:
        flow.index(from_csv(fp, field_resolver={'question': 'text'}))


if __name__ == '__main__':
    tutorial(8080)
```

If you run this, it should finish without errors. You won't see much yet because we are not showing anything after we
index.

To actually see something we need to specify how we will display it. For our tutorial we will do so in our browser.
After indexing, we will open a web browser to serve the static html files. We also need to configure and serve our Flow
on a specific port with the HTTP protocol so that the web browser can make requests to the Flow. So, we'll use the
parameter `port_expose` to configure the Flow and set the protocol to HTTP. Modify the function `tutorial` like so:

```{code-block} python
---
emphasize-lines: 13, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37
---
def tutorial(port_expose):
    class MyTransformer(Executor):
        @requests(on='/foo')
        def foo(self, **kwargs):
            print(f'foo is doing cool stuff: {kwargs}')
    
    class MyIndexer(Executor):
        @requests(on='/bar')
        def bar(self, **kwargs):
            print(f'bar is doing cool stuff: {kwargs}')
    
    flow = (
        Flow(cors=True)
            .add(name='MyTransformer', uses=MyTransformer)
            .add(name='MyIndexer', uses=MyIndexer)
    )
    with flow, open('dataset.csv') as fp:
        flow.index(from_csv(fp, field_resolver={'question': 'text'}))
    
        # switches the serving protocol to HTTP at runtime
        flow.protocol = 'http'
        flow.port_expose = port_expose
        url_html_path = 'file://' + os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 'static/index.html'
            )
        )
        try:
            webbrowser.open(url_html_path, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {url_html_path} manually'
            )
        flow.block()
```

```{admonition} See Also
:class: seealso
For more information on what the Flow is doing, and how to serve the Flow with `f.block()` and configure the protocol, 
check {ref}`the Flow fundamentals section <flow-cookbook>`.
```

```{admonition} Important
:class: important
Since we want to call our Flow from the browser, it's important to enable 
[Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) with `Flow(cors=True)`
```

Ok, so it seems that we have plenty of work done already. If you run this you will see a new tab open in your browser,
and there you will have a text box ready for you to input some text. However, if you try to enter anything you won't get
any results. This is because we are using dummy Executors. Our `MyTransformer` and `MyIndexer` aren't actually doing
anything. So far they only print a line when they are called. So we need real Executors.

## Create Executors

We will be creating our Executors in a separate file: `my_executors.py`.

### Sentence Transformer

First, let's import the following:

```python
from typing import Dict

from jina import Executor, DocumentArray, requests
from jina.types.arrays.memmap import DocumentArrayMemmap
from sentence_transformers import SentenceTransformer
```

Now, let's implement `MyTransformer`:

```python
class MyTransformer(Executor):
    """Transformer executor class """

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'paraphrase-mpnet-base-v2',
        device: str = 'cpu',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.model = SentenceTransformer(pretrained_model_name_or_path, device=device)
        self.model.to(device)

    @requests
    def encode(self, docs: 'DocumentArray', *args, **kwargs):
        import torch

        with torch.no_grad():
            texts = docs.get_attributes("text")
            embeddings = self.model.encode(texts, batch_size=32)
            for doc, embedding in zip(docs, embeddings):
                doc.embedding = embedding
```

`MyTransformer` exposes only one endpoint: `encode`. This will be called whenever we make a request to the Flow, either
on query or index. The endpoint will create embeddings for the indexed or query Documents so that they can be used to
get the closed matches.

```{admonition} Note
:class: note
Encoding is a fundamental concept in neural search. It means representing the data in a vectorial form (embeddings).
```

Encoding is performed through a sentence-transformers model (`paraphrase-mpnet-base-v2` by default). We get the text
attributes of docs in batch and then compute embeddings. Later, we set the embedding attribute of each Document.

### Simple Indexer

Now, let's implement our indexer (`MyIndexer`):

```python
class MyIndexer(Executor):
    """Simple indexer class """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArrayMemmap(self.workspace + '/indexer')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', **kwargs):
        """Append best matches to each document in docs

        :param docs: documents that are searched
        :param kwargs: other keyword arguments
        """
        docs.match(self._docs, metric='cosine', normalization=(1, 0), limit=1)
```


`MyIndexer` exposes 2 endpoints: `index` and `search`. To perform indexing, we use 
[`DocumentArrayMemmap`](https://docs.jina.ai/api/jina.types.arrays.memmap/#jina.types.arrays.memmap.DocumentArrayMemmap) 
which is a Jina data type. Indexing is a simple as adding the Documents to the `DocumentArrayMemmap`.

```{admonition} See Also
:class: seealso
Learn more about {ref}`DocumentArrayMemmap<documentarraymemmap-api>`.
```

To perform the search operation, we use the method `match` which will return the top match for the query Documents using
the cosine similarity.

```{admonition} See Also
:class: seealso
`.match` is a method of both `DocumentArray` and `DocumentArrayMemmap`. Learn more about it {ref}`in this section<match-documentarray>`.
```

To import the Executors, just add this to the imports:

``` python
from my_executors import MyTransformer, MyIndexer
```

## Put all together

Your `app.py` should now look like this:

```python
import os
import webbrowser
from pathlib import Path
from jina import Flow, Executor
from jina.logging.predefined import default_logger
from jina.types.document.generators import from_csv
from my_executors import MyTransformer, MyIndexer


def tutorial(port_expose):
    flow = (
        Flow(cors=True)
        .add(name='MyTransformer', uses=MyTransformer)
        .add(name='MyIndexer', uses=MyIndexer)
    )
    with flow, open('dataset.csv') as fp:
        flow.index(from_csv(fp, field_resolver={'question': 'text'}))

        # switch to REST gateway at runtime
        flow.protocol = 'http'
        flow.port_expose = port_expose
        url_html_path = 'file://' + os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 'static/index.html'
            )
        )
        try:
            webbrowser.open(url_html_path, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {url_html_path} manually'
            )
        flow.block()


if __name__ == '__main__':
    tutorial(8080)
```

And your directory should be:

    .
    └── tutorial                    
        ├── app.py          
        ├── my_executors.py         
        ├── static/         
        ├── our_flow.svg #This will be here if you used the .plot() function       
        └── dataset.csv

And we are done! If you followed all the steps, now you should have something like this in your browser:

```{figure} ../_static/results.png
:align: center
```

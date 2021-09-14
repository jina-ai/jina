# Covid-19 Chatbot Tutorial


We will use the {ref}`hello world chatbot <chatbot-helloworld>` for this tutorial. You can find the complete code [here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot) and we will go step by step.

At the end of this tutorial, you will have your own chatbot. You will use text as an input and get a text result as output. For this example, we will use a [covid dataset](https://www.kaggle.com/xhlulu/covidqa). You will understand how every part of this example works and how you can create new apps with different datasets on your own.

## Set-up & overview

We recommend creating a [new python virtual environment](https://docs.python.org/3/tutorial/venv.html), to have a clean install of Jina and prevent dependency clashing.

We can start by installing Jina:

``` shell
pip install jina
```

```{admonition} See Also
:class: seealso
For more information on installing Jina, refer to {ref}`installation page <install>`.
```

And we need the following dependencies:


``` shell
pip install click==7.1.2 transformers==4.1.1 torch==1.7.1
```

Once you have Jina and the dependencies installed, let's get a broad overview of the process we'll follow:

```{figure} ../../.github/images/flow.png
:align: center
```

You see from this image that you have your data at the beginning of this Flow process, and this can be any data type:

-   Text
-   Images
-   Audio
-   Video
-   Or any other type

In this case, we are using text, but it can be whatever data type you want.

Because our use case is very simple we don't need to process this data any further, and we can move straight on and encode our data into vectors then finally store those vectors, so they are ready for indexing and querying.

```{admonition} Note
:class: note
If you have a different use case or dataset you may need to process your data somehow (this is a very common task in machine learning)
```
## Tutorial

### Define data and work directories

We can start by creating an empty folder, I'll call mine `tutorial` and that's the name you'll see through the tutorial but feel free to use whatever you wish.

We will display our results in our browser, so download the static folder from 
[here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot/static), and paste it into your tutorial 
folder. This is only the CSS and HTML files to render our results. We will use a dataset in a `.csv` format. 
We'll use the [COVID](https://www.kaggle.com/xhlulu/covidqa) dataset from Kaggle. 

Download it under your project directory:
```shell
wget https://static.jina.ai/chatbot/dataset.csv
```

### Create a Flow

The very first concept you'll see in Jina is a Flow. You can see {ref}`here <flow-cookbook>` a more formal introduction of what it is, but for now, think of the Flow as a manager in Jina, it takes care of the all the tasks that will run on your application and each Flow object will take care of one real-world task.

To create a Flow you only need to import it from Jina. So open your favorite IDE, create an `app.py` file and let's start writing our code:

``` python
from jina import Flow
flow = Flow()
```

But this is an empty Flow. Since we want to encode our data and then index it, we need to add elements to it. The only things we add to a Flow are Executors. We will talk about them more formally later, but think of them as the elements that will do all the data processing you want.

### Add elements to a Flow

To add elements to your Flow you just need to use the `.add()` method. You can add as many pods as you wish.

``` python
from jina import Flow
flow = Flow().add().add()
```

And for our example, we need to add two `Executors`:

1.  A transformer (to encode our data)
2.  An indexer

So add the following to our code:

``` python
from jina import Flow
flow = (
        Flow()
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
    )
```

Right now we haven't defined `MyTransformer` or `MyIndexer`. Let's create some dummy Executors so we can try our app. These will not be our final Executors but just something basic to learn first.

### Create dummy Executors

Now we have a Flow with two Executors. Write the following in your code:

``` python
from jina import Executor, requests

class MyTransformer(Executor):
    @requests(on='/foo')
    def foo(self, **kwargs):
        print(f'foo is doing cool stuff: {kwargs}')
    
class MyIndexer(Executor):
    @requests(on='/bar')
    def bar(self, **kwargs):
        print(f'bar is doing cool stuff: {kwargs}')
```

We will have more complex Executors later. For now our two Executors are only printing a line.

So far it's a simple Flow but it is still useful to visualize it to make sure we have what we want.

### Visualize a Flow

By now, your code should look like this:

``` python
from jina import Flow, Document, Executor, requests
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
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
    )
```

If you want to visualize your Flow you can do that with `plot`. So add the `.plot()` function at the end of your Flow

``` python
from jina import Flow
flow = (
        Flow()
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
    )

flow.plot('our_flow.svg')
```

Let's run the code we have so far. If you try it, not much will happen since we are not indexing anything yet, but you will see the new file `our_flow.svg` created on your working folder, and if you open it you would see this:

```{figure} ../../.github/images/plot_flow1.svg
:align: center
```

You can see a Flow with two Executors, but what if you have many Executors? this can quickly become very messy, so it is better to name the Executors with `name='CoolName'`. So in our example, we use:

``` python
from jina import Flow
flow = (
        Flow()
        .add(name='MyTransformer', uses=MyTransformer)
        .add(name='MyIndexer', uses=MyIndexer)
    )

flow.plot('our_flow.svg')
```

Now if you run this, you should have a Flow that is more explicit:

```{figure} ../../.github/images/plot_flow2.svg
:align: center
```


### Use a Flow

Ok, we have our Flow created and visualized. Let's put it to use now. The correct way to use a Flow is to open it as a context manager, using the `with` keyword:

``` python
with flow:
    ...
```

Before we use it in our example, let's recap a bit of what we have seen:

````{list-table}
:header-rows: 1

* - Operation
  - Description
* - `flow = Flow()`
  - Create Flow
* - `flow.add().add()`
  - Add elements to Flow
* - `flow.plot()`
  - Visualize a Flow
* - ```python
    with flow:
        flow.index()
    ```
  - Use Flow as a context manager
````

In our example, we have a Flow with two Executors (`MyTransformer` and `MyIndexer`) and we want to use our Flow to index our data. But in this case, our data is a csv file. We need to open it first.

``` python
with flow, open('dataset.csv') as fp:
        pass            # You can here use the flow, e.g, index data
```

Now we have our Flow ready, we can start to index. But we can't just pass the dataset in the original format to our Flow. We need to create Documents with the data we want to use.

```{admonition} See Also
:class: seealso
`Document` is the basic data type in Jina. It can hold different types of information. You can learn more about 
`Document` {ref}`in this section <document-cookbook>`
```


### Create documents from a csv file

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

So what happened there? We created a generator of Documents `docs`, and we used [from_csv](https://docs.jina.ai/api/jina.types.document.generators/#jina.types.document.generators.from_csv) to load our dataset. We use `field_resolver` to map the text from our dataset to the Document attributes.

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
`flow.index` will send the data to the `/index` endpoint. However, both of the added executors do not have an `/index` 
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
This simply means that no endpoint will be triggered by `flow.index`. Besides, our executors are dummy and still do not 
have logic to index data. Later, we will modify executors so that calling `flow.index` does indeed store the dataset.
````

Let's put the executors and the flow together and re-organize our code a little bit. First, we should import everything 
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
`tutorial` accepts 1 parameters that we'll need later: 
`port_expose` (the port used to expose our flow)

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
After indexing, we will open a web browser to serve the static html files. We also need to configure and serve our flow 
on a specific port with the HTTP protocol so that the web browser can make requests to the flow. So, we'll use the 
parameter `port_expose` to configure the flow and set the protocol to HTTP.
Modify the function `tutorial` like so:

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
For more information on what the Flow is doing, and how to serve the flow with `f.block()` and configure the protocol, 
check {ref}`the Flow fundamentals section <flow-cookbook>`.
```

```{admonition} Important
:class: important
Since we want to call our Flow from the browser, it's important to enable 
[Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) with `Flow(cors=True)`
```



Ok, so it seems that we have plenty of work done already. If you run this you will see a new tab open in your browser, 
and there you will have a text box ready for you to input some text. However, if you try to enter anything you won't 
get any results. This is because we are using dummy Executors. Our `MyTransformer` and `MyIndexer` aren't actually 
doing anything. So far they only print a line when they are called. So we need real Executors.

## Creating Executors
We will be creating our Executors in a separate file: `my_executors.py`.

First, let's import the following:
```python
from typing import Optional, Dict

import numpy as np
import torch
from jina import Executor, DocumentArray, requests
from jina.types.arrays.memmap import DocumentArrayMemmap
from transformers import AutoModel, AutoTokenizer
```

Now, let's implement `MyTransformer`:
```python
class MyTransformer(Executor):
    """Transformer executor class """

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'sentence-transformers/paraphrase-mpnet-base-v2',
        base_tokenizer_model: Optional[str] = None,
        pooling_strategy: str = 'mean',
        layer_index: int = -1,
        max_length: Optional[int] = None,
        acceleration: Optional[str] = None,
        embedding_fn_name: str = '__call__',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.base_tokenizer_model = (
            base_tokenizer_model or pretrained_model_name_or_path
        )
        self.pooling_strategy = pooling_strategy
        self.layer_index = layer_index
        self.max_length = max_length
        self.acceleration = acceleration
        self.embedding_fn_name = embedding_fn_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_tokenizer_model)
        self.model = AutoModel.from_pretrained(
            self.pretrained_model_name_or_path, output_hidden_states=True
        )
        self.model.to(torch.device('cpu'))

    def _compute_embedding(self, hidden_states: 'torch.Tensor', input_tokens: Dict):
        import torch

        fill_vals = {'cls': 0.0, 'mean': 0.0, 'max': -np.inf, 'min': np.inf}
        fill_val = torch.tensor(
            fill_vals[self.pooling_strategy], device=torch.device('cpu')
        )

        layer = hidden_states[self.layer_index]
        attn_mask = input_tokens['attention_mask'].unsqueeze(-1).expand_as(layer)
        layer = torch.where(attn_mask.bool(), layer, fill_val)

        embeddings = layer.sum(dim=1) / attn_mask.sum(dim=1)
        return embeddings.cpu().numpy()

    @requests
    def encode(self, docs: 'DocumentArray', *args, **kwargs):
        import torch

        with torch.no_grad():

            if not self.tokenizer.pad_token:
                self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                self.model.resize_token_embeddings(len(self.tokenizer.vocab))

            input_tokens = self.tokenizer(
                docs.get_attributes('content'),
                max_length=self.max_length,
                padding='longest',
                truncation=True,
                return_tensors='pt',
            )
            input_tokens = {
                k: v.to(torch.device('cpu')) for k, v in input_tokens.items()
            }

            outputs = getattr(self.model, self.embedding_fn_name)(**input_tokens)
            if isinstance(outputs, torch.Tensor):
                return outputs.cpu().numpy()
            hidden_states = outputs.hidden_states

            embeds = self._compute_embedding(hidden_states, input_tokens)
            for doc, embed in zip(docs, embeds):
                doc.embedding = embed
```

`MyTransformer` exposes only one endpoint: `encode`. This will be called whenever we make a request to the flow, either 
on query or index. The endpoint will create embeddings for the indexed or query documents so that they can be used 
to get the closed matches.
```{admonition} Note
:class: note
Encoding is a fundamental concept in neural search. It means representing the data in a vectorial form (embeddings).
```

Encoding is performed through a transformers model (`sentence-transformers/paraphrase-mpnet-base-v2` by default).

Then, we can implement our indexer (`MyIndexer`):
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
[DocumentArrayMemmap](https://docs.jina.ai/api/jina.types.arrays.memmap/#jina.types.arrays.memmap.DocumentArrayMemmap)` 
which is a Jina data type. Indexing is a simple as adding the documents to the `DocumentArrayMemmap`.

```{admonition} See Also
:class: seealso
Learn more about {ref}`DocumentArrayMemmap<documentarraymemmap-api>`.
```
To perform the search operation, we use the method `match` which will return the top match for the query documents 
using the cosine similarity.

```{admonition} See Also
:class: seealso
`.match` is a method of both `DocumentArray` and `DocumentArrayMemmap`. Learn more about it {ref}`in this section<match-documentarray>`.
```

To import the executors, just add this to the imports:

``` python
from my_executors import MyTransformer, MyIndexer
```

And remove the dummy executors we made. Your `app.py` should now look like this:

``` python
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
    └── project                    
        ├── app.py          
        ├── my_executors.py         
        ├── static/         
        ├── our_flow.svg #This will be here if you used the .plot() function       
        └── dataset.csv

And we are done! If you followed all the steps, now you should have something like this in your browser:

```{figure} ../../.github/images/results.png
:align: center
```

There are still a lot of concepts to learn. So stay tuned for our next tutorials.

If you have any issues following this tutorial, you can always get support from our [Slack community](https://slack.jina.ai/)

## Community


-   [Slack community](https://slack.jina.ai/) - a communication platform for developers to discuss Jina.
-   [LinkedIn](https://www.linkedin.com/company/jinaai/) - get to know Jina AI as a company and find job opportunities.
-   [Twitter](https://twitter.com/JinaAI_) - follow us and interact with us using hashtag #JinaSearch.
-   [Company](https://jina.ai) - know more about our company, we are fully committed to open-source!

## License


Copyright (c) 2021 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. See [LICENSE](https://github.com/jina-ai/jina/blob/master/LICENSE) for the full license text.
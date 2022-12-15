# Fuzzy String Matching in 30 Lines


````{admonition} Different behavior on Jupyter Notebook
:class: warning
Be aware of the following when running this tutorial in jupyter notebook. Some python built-in attributes such as `__file__` do not exist. You can change `__file__` for any other file path existing in your system.
````


Now that you understand all fundamental concepts, let's practice the learnings and build a simple end-to-end demo.

We will use Jina to implement a fuzzy search solution on source code: given a snippet source code and a query, find all lines that are
similar to the query. It is like `grep` but in fuzzy mode.

````{admonition} Preliminaries
:class: hint

- [Character embedding](https://en.wikipedia.org/wiki/Word_embedding)
- [Pooling](https://computersciencewiki.org/index.php/Max-pooling_/_Pooling)
- [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance)
````

## Client-Server architecture

```{figure} ../../.github/2.0/simple-arch.svg
:align: center
```

## Server

### Character embedding

Let's first build a simple Executor for character embedding:

```python
import numpy as np
from jina import DocumentArray, Executor, requests


class CharEmbed(Executor):  # a simple character embedding with mean-pooling
    offset = 32  # letter `a`
    dim = 127 - offset + 1  # last pos reserved for `UNK`
    char_embd = np.eye(dim) * 1  # one-hot embedding for all chars

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            r_emb = [
                ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1)
                for c in d.text
            ]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling
```

### Indexer with Euclidean distance

```python
from jina import DocumentArray, Executor, requests


class Indexer(Executor):
    _docs = DocumentArray()  # for storing all documents in memory

    @requests(on='/index')
    def foo(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)  # extend stored `docs`

    @requests(on='/search')
    def bar(self, docs: DocumentArray, **kwargs):
        docs.match(self._docs, metric='euclidean', limit=20)
```

### Put it together in a Flow

```python
from jina import Flow

f = (
    Flow(port_expose=12345, protocol='http', cors=True)
    .add(uses=CharEmbed, replicas=2)
    .add(uses=Indexer)
)  # build a Flow, with 2 shard CharEmbed, tho unnecessary
```

### Start the Flow and index data

```python
from jina import Document

with f:
    f.post(
        '/index', (Document(text=t.strip()) for t in open(__file__) if t.strip())
    )  # index all lines of _this_ file
    f.block()  # block for listening request
```

```{caution}

`open(__file__)` means open the current file and use it for indexing. Note in some enviroment such as Jupyter Notebook 
and Google Colab, `__file__` is not defined. In this case, you may want to replace it to `open('my-source-code.py')`. 
```

## Query via SwaggerUI

Open `http://localhost:12345/docs` (an extended Swagger UI) in your browser, click <kbd>/search</kbd> tab and input:

```json
{
  "data": [
    {
      "text": "@requests(on=something)"
    }
  ]
}
```

That means, **we want to find lines from the above code snippet that are most similar to `@request(on=something)`.**Now
click <kbd>Execute</kbd> button!


```{figure} ../../.github/swagger-ui-prettyprint1.gif
:align: center
```


## Query from Python

Let's do it in Python then! Keep the above server running and start a simple client:

```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["euclidean"].value:2f}: "{d.text}"')


c = Client(protocol='http', port=12345)  # connect to localhost:12345
c.post('/search', Document(text='request(on=something)'), on_done=print_matches)
```

, which prints the following results:

```text
         Client@1608[S]:connected to the gateway at localhost:12345!
[0]0.168526: "@requests(on='/index')"
[1]0.181676: "@requests(on='/search')"
[2]0.218218: "from jina import Document, DocumentArray, Executor, Flow, requests"
```


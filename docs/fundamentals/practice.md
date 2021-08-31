## Practice
<sup>💡 Preliminaries: <a href="https://en.wikipedia.org/wiki/Word_embedding">character embedding</a>, <a href="https://computersciencewiki.org/index.php/Max-pooling_/_Pooling">pooling</a>, <a href="https://en.wikipedia.org/wiki/Euclidean_distance">Euclidean distance</a></sup>

After learning Jina fundamentals, let's apply what you learnt through an example.
In this example, we will use a simple character embedding encoder with mean-pooling to encode document text.
Therefore, we will have a flow that looks like this: 

```{figure} ../../.github/2.0/simple-arch.svg
:align: center
```
1️⃣ Copy-paste the minimum example below and run it:

```python
import numpy as np
from jina import Document, DocumentArray, Executor, Flow, requests

class CharEmbed(Executor):  # a simple character embedding with mean-pooling
    offset = 32  # letter `a`
    dim = 127 - offset + 1  # last pos reserved for `UNK`
    char_embd = np.eye(dim) * 1  # one-hot embedding for all chars

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1) for c in d.text]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling

class Indexer(Executor):
    _docs = DocumentArray()  # for storing all documents in memory

    @requests(on='/index')
    def foo(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)  # extend stored `docs`

    @requests(on='/search')
    def bar(self, docs: DocumentArray, **kwargs):
         docs.match(self._docs, metric='euclidean', limit=20)

f = Flow(port_expose=12345, protocol='http', cors=True).add(uses=CharEmbed, parallel=2).add(uses=Indexer)  # build a Flow, with 2 parallel CharEmbed, tho unnecessary
with f:
    f.post('/index', (Document(text=t.strip()) for t in open(__file__) if t.strip()))  # index all lines of _this_ file
    f.block()  # block for listening request
```

2️⃣ Open `http://localhost:12345/docs` (an extended Swagger UI) in your browser, click <kbd>/search</kbd> tab and input:

```json
{"data": [{"text": "@requests(on=something)"}]}
```

That means, **we want to find lines from the above code snippet that are most similar to `@request(on=something)`.**  Now click <kbd>Execute</kbd> button!

<p align="center">
<img src="https://github.com/jina-ai/jina/blob/master/.github/swagger-ui-prettyprint1.gif?raw=true" alt="Jina Swagger UI extension on visualizing neural search results" width="85%">
</p>

3️⃣ Not a GUI person? Let's do it in Python then! Keep the above server running and start a simple client:


```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["euclidean"].value:2f}: "{d.text}"')


c = Client(protocol='http', port_expose=12345)  # connect to localhost:12345
c.post('/search', Document(text='request(on=something)'), on_done=print_matches)
```


which prints the following results:

```text
         Client@1608[S]:connected to the gateway at localhost:12345!
[0]0.168526: "@requests(on='/index')"
[1]0.181676: "@requests(on='/search')"
[2]0.192049: "query.matches = [Document(self._docs[int(idx)], copy=True, score=d) for idx, d in enumerate(dist)]"
```
<sup>😔 Doesn't work? Our bad! <a href="https://github.com/jina-ai/jina/issues/new?assignees=&labels=kind%2Fbug&template=---found-a-bug-and-i-solved-it.md&title=">Please report it here.</a></sup>
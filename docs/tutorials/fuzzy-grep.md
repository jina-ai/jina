# 30줄 안의 Fuzzy 문자열 매칭


````{admonition} Different behavior on Jupyter Notebook
:class: warning
Be aware of the following when running this tutorial in jupyter notebook. Some python built-in attributes such as `__file__` do not exist. You can change `__file__` for any other file path existing in your system.
````


이제 모든 개념을 이해 했으므로 학습 내용을 연습하고 간단한 end-to-end 데모를 만들어 보겠습니다.

우리는 소스 코드에 fuzzy 검색 솔루션을 구현하기 위해 Jina를 사용할 것입니다.
즉, 소스 코드 조각과 query가 주어지면 query와 유사한 모든 줄을 찾습니다. 이것은 `grep`과 같지만 fuzzy 모드 입니다.

````{admonition} Preliminaries
:class: hint

- [Character embedding](https://en.wikipedia.org/wiki/Word_embedding)
- [Pooling](https://computersciencewiki.org/index.php/Max-pooling_/_Pooling)
- [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance)
````

## 클라이언트-서버 구조

```{figure} ../../.github/2.0/simple-arch.svg
:align: center
```

## 서버

### 문자 임베딩

먼저 문자 임베딩을 위한 간단한 Executor를 구현해봅시다:

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
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else (self.dim - 1) for c in d.text]
            d.embedding = self.char_embd[r_emb, :].mean(axis=0)  # average pooling
```

### 유클리드 거리가 있는 인덱서

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

### Flow안에 함께 넣는다

```python
from jina import Flow

f = (Flow(port_expose=12345, protocol='http', cors=True)
        .add(uses=CharEmbed, replicas=2)
        .add(uses=Indexer))  # build a Flow, with 2 shard CharEmbed, tho unnecessary

```

### Flow와 인덱스 데이터를 시작한다

```python
from jina import Document

with f:
    f.post('/index', (Document(text=t.strip()) for t in open(__file__) if t.strip()))  # index all lines of _this_ file
    f.block()  # block for listening request
```

```{caution}

`open(__file__)` means open the current file and use it for indexing. Note in some enviroment such as Jupyter Notebook 
and Google Colab, `__file__` is not defined. In this case, you may want to replace it to `open('my-source-code.py')`. 
```

## SwaggerUI를 통한 Query

`http://localhost:12345/docs` (an extended Swagger UI) 를 당신의 브라우저에서 여세요. <kbd>/search</kbd> 탭과 입력값을 클릭하세요:

```json
{
  "data": [
    {
      "text": "@requests(on=something)"
    }
  ]
}
```

즉, **우리는 가장 `@request(on=something)`와 비슷한 부류의 라인을 위의 코드에서 찾기를 바랍니다. **이제 <kbd>Execute</kbd>버튼을 누르세요!

```{figure} ../../.github/swagger-ui-prettyprint1.gif
:align: center
```


## Python에서 나온 Query 

이제 파이썬으로 해봅시다. 위의 서버를 계속 실행하고, 간단한 클라이언트를 시작합니다:

```python
from jina import Client, Document
from jina.types.request import Response


def print_matches(resp: Response):  # the callback function invoked when task is done
    for idx, d in enumerate(resp.docs[0].matches[:3]):  # print top-3 matches
        print(f'[{idx}]{d.scores["euclidean"].value:2f}: "{d.text}"')


c = Client(protocol='http', port=12345)  # connect to localhost:12345
c.post('/search', Document(text='request(on=something)'), on_done=print_matches)
```

,이러한 결과를 출력한다:

```text
         Client@1608[S]:connected to the gateway at localhost:12345!
[0]0.168526: "@requests(on='/index')"
[1]0.181676: "@requests(on='/search')"
[2]0.218218: "from jina import Document, DocumentArray, Executor, Flow, requests"
```


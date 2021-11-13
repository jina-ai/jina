# Transformer를 통한 챗봇 질의 응답

```{article-info}
:avatar: avatars/susana.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Susana @ Jina AI
:date: June 15, 2021
```
저희는 이 튜토리얼을 위해 {ref}`hello world chatbot <chatbot-helloworld>` 를 사용할 것 입니다.
전체 코드를 [여기](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot) 에서 찾을 수 있고, 차근차근 진행 해 볼 것입니다.

이 튜토리얼이 끝나는 지점에서, 당신은 당신만의 chatbot을 소유하게 될 것입니다. 당신은 텍스트를 입력으로서 사용하고 텍스트를 결과값으로 받게 됩니다. 예를 들어, 우리는 [covid dataset](https://www.kaggle.com/xhlulu/covidqa)를 이용할 것 입니다. 당신은 이 예제의 모든 부분이 어떻게 작동하는지와 다른 데이터셋으로 새 앱을 직접 만드는 방법을 이해 하게 될 것 입니다.

## 데이터 및 작업 디렉토리 정의

빈 폴더를 만드는 것으로 시작할 수 있습니다. 저는 이걸 `튜토리얼`이라고 부를 것이고, 당신이 튜토리얼을 통해 볼 수 있는 이름입니다. 원하는 것 어떤 것이든 자유롭게 사용하세요.

우리는 브라우저에 결과값을 표기할 것이기 때문에 [여기](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot/static)에서 정적 폴더를 다운로드 해주시고, 당신의 튜토리얼 폴더로 붙여넣기 하세요. 이것은 결과를 옮기기 위한 CSS , HTML 파일입니다. This is only the CSS and HTML files to render our results.우리는 `.csv` 포멧으로 된 데이터셋을 이용할 것 입니다. kaggle에 있는 [COVID](https://www.kaggle.com/xhlulu/covidqa) 데이터 셋을 사용하겠습니다.

당신의 `튜토리얼` 디렉토리 아래에 다운로드 하세요:

```shell
wget https://static.jina.ai/chatbot/dataset.csv
```

## csv 파일에서 문서 생성

Jina에서 문서 생성을 하기 위해서는, 이렇게 합니다:

``` python
doc = Document(content='hello, world!')
```

이 경우, 문서 내용은 사용하고자 하는 데이터셋이어야 합니다:

``` python
from jina.types.document.generators import from_csv
with open('dataset.csv') as fp:
    docs = from_csv(fp, field_resolver={'question': 'text'})
```

그래서 무슨 일이 일어났나요? 우리는 문서 생성기 `docs`를 만들었고, [from_csv](https://docs.jina.ai/api/jina.types.document.generators/#jina.types.document.generators.from_csv)를 사용하여 데이터셋을 불러왔습니다. 우리는 `field_resolver`를 사용하여 데이터셋의 텍스트를 document 속성에 매핑합니다.
used [from_csv](https://docs.jina.ai/api/jina.types.document.generators/#jina.types.document.generators.from_csv) to

마지막으로, 이와 같이 이전 두 단계 ( 데이터 셋을 문서에 로드하고 컨텍스트를 시작 )와 인덱스를 결합할 수 있습니다 : 

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

## Flow 생성

Executors와 Flow를 통합하고 코드를 약간 재구성 해보겠습니다. 먼저, 우리는 우리가 필요한 모든 것을 임포트 합니다:

``` python
import os
import webbrowser
from pathlib import Path
from jina import Flow, Executor, requests
from jina.logging.predefined import default_logger
from jina.types.document.generators import from_csv
```

그러려면 지금까지 해왔던 모든 코드를 담은 `메인` 과 `튜토리얼` 기능이 있어야 합니다.
`튜토리얼`은 후에 필요한 한가지 파라미터를 사용합니다:
`port_expose` (Flow를 노출 시키는데 사용되는 포트)

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

## Executors 만들기

별개의 파일에 Executors를 생성합니다:`my_executors.py`.

### 문장 변환기

먼저, 밑의 것들을 임포트 합니다:

```python
from typing import Dict

from jina import Executor, DocumentArray, requests
from jina.types.arrays.memmap import DocumentArrayMemmap
from sentence_transformers import SentenceTransformer
```

자 이제 Now,`MyTransformer`를 구현 해봅시다:

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

### 간단한 Indexer

자, 이제 indexer (`MyIndexer`)를 구현 해봅시다:

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

검색 기능을 수행하기 위해선, 코사인 유사도를 사용하여 query Document에서 가장 높은 매칭을 리턴하는 `match` 메소드를 사용합니다.

```{admonition} See Also
:class: seealso
`.match` is a method of both `DocumentArray` and `DocumentArrayMemmap`. Learn more about it {ref}`in this section<match-documentarray>`.
```

Executors를 임포트 하기 위해선, 이것들을 추가 하세요:

``` python
from my_executors import MyTransformer, MyIndexer
```

## 모든 것을 한 곳에 둡니다

당신의 `app.py` 는 이런 모양이 되어야 합니다:

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

그러면 당신의 디렉토리는 다음과 같은 모양이 됩니다:

    .
    └── tutorial                    
        ├── app.py          
        ├── my_executors.py         
        ├── static/         
        ├── our_flow.svg #This will be here if you used the .plot() function       
        └── dataset.csv

이제 끝났습니다. 모든 과정을 잘 따라 왔다면, 당신의 브라우저에는 다음과 같은 것이 있을 것입니다:browser:

```{figure} ../_static/results.png
:align: center
```

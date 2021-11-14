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

이 프로그램을 실행하면 오류 없이 끝날 수 있습니다. 인덱싱 후에는 아무것도 볼 수 없기 때문에 아직은 뭔가 많이 보이지는 않습니다.

실제로 보기 위해서는 어떻게 표시할것인지 방법을 지정해야합니다. 튜토리얼의 경우 브라우저에서 해당 작업을 수행합니다.
인덱싱 후, 웹 브라우저를 열어 정적 html 파일을 제공합니다. 또한 웹 브라우저가 Flow에 요청할 수 있도록 HTTP 프로토콜을 사용하여 특정 포트에 Flow를 구성하고 서비스 해야합니다. 따라서 파라미터  `port_expose`를 사용하여 Flow를 구성하고 프로토콜을 HTTP로 설정합니다. 
다음과 같이 기능 `튜토리얼`을 수정합니다 : 

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

지금까지 많은 일을 끝냈습니다. 이걸 실행하면 브라우저에 열려 있는 새 탭이 표시 되고 텍스트를 입력할 수 있는 텍스트 상자가 준비됩니다. 
그러나 입력하려고 하면 어떠한 결과도 얻을 수 없습니다. 이것은 우리가 더미 Executor을 사용하고 있기 때문입니다.
`MyTransformer` 와 `MyIndexer` 는 실제로 아무런 동작도 하지 않고 있습니다.
지금까지 그들은 호명될 때만 한 줄을 프린트 합니다. 그래서 우리는 진짜 Executor가 필요합니다.

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

`MyIndexer`에는 2가지 엔드포인트가 표시 됩니다 : `인덱스` 와 `검색`. 인덱싱을 수행하기 위해서 우리는 Jina 데이터 타입인 [`DocumentArrayMemmap`](https://docs.jina.ai/api/jina.types.arrays.memmap/#jina.types.arrays.memmap.DocumentArrayMemmap)
을 사용합니다.
인덱싱은 Document를 `DocumentArrayMemmap`에 추가하는 간단한 방법입니다.

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

이제 끝났습니다. 모든 과정을 잘 따라 왔다면, 당신의 브라우저에는 다음과 같은 것이 있을 것입니다:

```{figure} ../_static/results.png
:align: center
```

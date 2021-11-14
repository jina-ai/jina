# Master Executor: Zero에서 Hub까지

```{article-info}
:avatar: avatars/cristian.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Cristian @ Jina AI
:date: Sept. 10, 2021
```

이것은 당신의 Executor를 생성하거나 기존 Executor를 사용하는 방법에 대한 단계별 설명입니다.

[comment]: <> (TODO add link to the chatbot tutorial when it's moved here )

[comment]: <> (Last time we talked about how to create the [hello world chatbot]&#40;https://jina.ai/tutorial.html&#41;, but we didn't go much into Executors' details. Let's take a look at them now.)

우리는 간단한 기록 Executor를 만들 것입니다. 이것이 문서에 도달하면 문서 정보를 기록하고 파일에 저장합니다. 또한 우리는 Executor를 나중에 사용하기 위해 Jina Hub로 푸시하는 방법도 살펴볼 것입니다.

## 설정과 개요

Jina를 새로 설치하고 종속성 충돌을 방지하기 위해 [새로운 Python 가상 환경](https://docs.python.org/3/tutorial/venv.html)을 만드는 것이 좋습니다.

먼저 Jina를 설치하여 시작할 수 있습니다:

 ```bash
pip install jina
 ```

Jina 설치에 대한 자세한 내용은 [ref](https://github.com/jina-ai/jina/blob/master/docs/get-started) `페이지의 <install>` 을 참조하세요.

## 나의 Executor 만들기

당신의 Executor를 만들려면 터미널에서 다음 명령어를 실행하기만 하면 됩니다: 

```shell
jina hub new
```

Wizard가 당신에게 Executor에 대해 몇 가지 질문을 할 것입니다. 기본 설정의 경우, 두 가지 질문이 표시됩니다:  

- Executor의 이름 
- 저장되어야 할 곳
 
이 튜토리얼의 경우, 우리는 **RequestLogger** 라고 부르겠습니다. 그리고 당신은 이 프로젝트를 당신이 원하는 곳에 저장할 수 있습니다. Wizard는 고급 설정을 원하는지 물어볼 것이지만, 이 튜토리얼에서는 필요하지 않습니다.

### Logger Executor

Wizard를 따라 가면 폴더 구조가 준비됩니다. 우리는 `executor.py` 파일을 가지고 시작할 수 있습니다. 해당 파일을 열고, 다음을 import합니다.

```python
import os
import time
from typing import Dict

from jina import Executor, DocumentArray, requests
from jina.logging.logger import JinaLogger
```

그런 다음 우리는 `Executor` 의 기본 클래스를 상속하는 클래스를 만들 것입니다. 우리는 이것을 `RequestLogger` 라고 부르겠습니다.

```{admonition} Important
:class: important
 
You always need to inherit from the `Executor` class, in order for the class to be properly registered into Jina.
```

```python
class RequestLogger(Executor):
```

우리의 Executor는 두 가지 메서드를 가집니다: 하나는 생성자를 위한 것이고, 다른 하나는 실제 logging을 위한 것입니다.

```python
class RequestLogger(Executor):    
    def __init__(self, **args, **kwargs):
        # Whatever you need for our constructor

    def log():
        # Whatever we need for our logging
```

작업할 문서의 수를 지정하는 것이 도움이 될 수 있으므로 이를 생성자의 인자로 직접 전달합니다.

``` python
de __init__(self,
                default_log_docs: int = 1,      
                # here you can pass whatever other arguments you need
                *args, **kwargs):     
``` 


```{admonition} Important
:class: important

You need to do this before writing any custom logic. It's required in order to register the parent class, which instantiates special fields and methods.
```

```python
super().__init__(*args, **kwargs)
```

이제 생성자 메서드를 만들기 시작합니다. `default_log_docs` 는 인자로 받은 값으로 설정합니다:

```python
self.default_log_docs = default_log_docs
```

logging을 위해 우리는 `JinaLogger` 의 인스턴스를 생성해야 합니다. 또한 log 파일을 저장할 경로를 지정해야 합니다.

```python
self.logger = JinaLogger('req_logger')
self.log_path = os.path.join(self.workspace, 'log.txt')
```

```{admonition} Note
:class: note

`self.workspace` will be provided by the `Executor` parent class.
```

그리고 마지막으로 우리는 파일이 존재하지 않는 경우에 대비하여 파일을 만들어야 합니다.

```python
if not os.path.exists(self.log_path):
    with open(self.log_path, 'w'): pass
```

자, 그것이 우리의 생성자에 대한 것입니다. 지금쯤이면 우리는 다음과 같은 것이 있어야 합니다:

```python
class RequestLogger(Executor):                                                                      # needs to inherit from Executor
    def __init__(self,
                default_log_docs: int = 1,                                                          # number of documents to log
                *args, **kwargs):                                                                   # *args and **kwargs are required for Executor
        super().__init__(*args, **kwargs)                                                           # before any custom logic
        self.default_log_docs = default_log_docs
        self.logger = JinaLogger('req_logger')                                                      # create instance of JinaLogger
        self.log_path = os.path.join(self.workspace, 'log.txt')                                     # set path to save the log.txt
        if not os.path.exists(self.log_path):                                                       # check the file doesn't exist already
            with open(self.log_path, 'w'): pass
```

이제 우리는 우리의 `log` 메서드를 생성할 수 있습니다. 가장 먼저 `@requests` 데코레이터가 필요합니다. 이것은 함수가 호출될 때 엔드포인트에서 `Flow` 와 통신하기 위한 것입니다. `@requests` 를 엔드포인트 없이 사용하므로 모든 요청에서 함수를 호출합니다:

```python
@requests
def log(self, 
        docs: Optional[DocumentArray],
        parameters: Dict,
        **kwargs):
```

여기 있는 내용에 주목하는 것이 중요합니다. 

```{admonition} Important
:class: important

It's not possible to redefine the interface of the public methods decorated by `@requests`. You can't change the name of these arguments. To see exactly which parameters you can use, check {ref}`here <executor-method-signature>`.
```

만약 `/index` 시간에만 당신의 `log` 함수를 호출하려면, 다음과 같이 `on=` 를 이용하여 엔드포인트를 지정하세요:

```{code-block} python
---
emphasize-lines: 1
---
@requests(on='/index')
def log(self,
        docs: Optional[DocumentArray],
        parameters: Dict,
        **kwargs):
```

데코레이터를 사용하는 방법에 대한 자세한 내용은 {ref}`the documentation <executor-request-parameters>` 를 참조하세요. 이 예시에서는 모든 요청에 대해 `log` 함수를 호출할 것이므로 엔드포인트를 지정하지 않습니다.

이제 우리는 함수에 로직을 추가할 수 있습니다. 먼저 일부 정보를 표시하는 행을 출력합니다. 그런 다음 문서에서 세부 정보를 저장합니다:

```python
self.logger.info('Request being processed...')
nr_docs = int(parameters.get('log_docs', self.default_log_docs))         # accesing parameters (nr are passed as float due to Protobuf)
with open(self.log_path, 'a') as f:
    f.write(f'request at time {time.time()} with {len(docs)} documents:\n')
    for i, doc in enumerate(docs):
        f.write(f'\tsearching with doc.id {doc.id}. content = {doc.content}\n')
        if i + 1 == nr_docs:
            break
```

여기에서 당신의 Executor에 필요한 로직을 설정할 수 있습니다. 이제 코드는 다음과 같아야 합니다:

```python
import os
import time
from typing import Dict, Optional

from jina import Executor, DocumentArray, requests
from jina.logging.logger import JinaLogger


class RequestLogger(Executor):                                                                      # needs to inherit from Executor
    def __init__(self,
                default_log_docs: int = 1,                                                          # your arguments
                *args, **kwargs):                                                                   # *args and **kwargs are required for Executor
        super().__init__(*args, **kwargs)                                                           # before any custom logic
        self.default_log_docs = default_log_docs
        self.logger = JinaLogger('req_logger')
        self.log_path = os.path.join(self.workspace, 'log.txt')
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w'): pass

    @requests                                                                                       # decorate, by default it will be called on every request
    def log(self,                                                                                   # arguments are automatically received
            docs: Optional[DocumentArray],
            parameters: Dict,
            **kwargs):
        self.logger.info('Request being processed...')

        nr_docs = int(parameters.get('log_docs', self.default_log_docs))                            # accesing parameters (nr are passed as float due to Protobuf)
        with open(self.log_path, 'a') as f:
            f.write(f'request at time {time.time()} with {len(docs)} documents:\n')
            for i, doc in enumerate(docs):
                f.write(f'\tsearching with doc.id {doc.id}. content = {doc.content}\n')
                if i + 1 == nr_docs:
                    break
```

이것이 끝입니다. 우리는 우리가 전달한 모든 문서를 가져오고 기록하는 `Executor` 가 있습니다. 

자, 이제 이것을 어떻게 앱에서 사용할 수 있을까요?

### Executor를 Hub로 푸시하기

우리는 Executor를 앱에서 직접 사용할 수도 있지만, 여기서는 더 많은 사람들과 공유하거나 나중에 사용할 수 있도록 Jina Hub에 푸시하는 방법을 살펴보겠습니다. 

첫 번째 단계는 `manifest.yml` 과 `config.yml` 파일이 여전히 관련성이 있는지 확인하는 것입니다. 이 파일에 들어있는 데이터가 당신의 Executor의 목적에 맞는지 확인하세요.

확인을 위해, 터미널에서 `executor.py` 파일이 들어있는 폴더를 열어야 합니다. 따라서 튜토리얼의 경우 `RequestLogger` 폴더 내에서 터미널을 열고, 다음을 입력하기만 하면 됩니다:

```bash
jina hub push --public .
```

이것은 당신이 당신의 Executor를 Jina Hub에 공개적으로 푸시한다는 의미입니다. 마지막 점은 현재 당신의 경로를 사용한다는 뜻입니다. 해당 명령어를 실행하고 나면 다음과 같이 나타나야 합니다:

```{figure} ../../.github/images/push-executor.png
:align: center
```

```{admonition} Note
:class: note

Since we pushed our Executor using the `--public` flag, the only thing we will use is the ID. In this case, it's `zsor7fe6`. Refer to {ref}`Jina Hub usage <jina-hub-usage>`.
```

### 당신의 Executor를 사용하세요

방금 작성한 Executor를 사용하기 위한 Jina Flow를 만들어 봅시다. `RequestLogger` 와 동일한 폴더에 `app.py` 를 만듭니다. `main` 함수를 만들기 전에 `Flow`, `DocumentArray`, `Document` 를 import합니다:

```python
from jina import Flow, DocumentArray, Document

def main():
    # We'll have our Flow here

if __name__ == '__main__':
    main()
```

방금 생성한 Executor는 우리가 전달하는 모든 문서를 기록할 것입니다. 따라서 먼저 몇 가지 문서를 만들어야 합니다. 우리는 이것을 `main()` 에서 하겠습니다.

```python
def main():
    docs = DocumentArray()
    docs.append(Document(content='I love cats'))                # creating documents
    docs.append(Document(content='I love every type of cat'))
    docs.append(Document(content='I guess dogs are ok'))
```

하나의 `DocumentArray` 에 3개의 문서가 있습니다. 이제 `Flow` 를 생성하고 우리가 만든 Executor를 추가해 봅시다. 우리는 이것을 푸시할 때 얻은 ID로 참조할 것입니다(제 경우에는 `zsor7fe6` 이었습니다):

```python
flow = Flow().add(                                              
        uses='jinahub+docker://zsor7fe6',                   # here we choose to use the Executor inside a docker container
        uses_with={                                         # RequestLogger arguments
            'default_log_docs': 3
        },
        volumes='workspace:/internal_workspace',            # mapping local folders to docker instance folders
        uses_metas={                                        # Executor (parent class) arguments
            'workspace': '/internal_workspace',             # this should match the above
        },
    )
```

자세한 내용은 다음과 같습니다:

```python
uses='jinahub+docker://zsor7fe6',
```

여기서 당신은 Executor의 이미지를 지정하기 위해 `uses=` 를 사용합니다. 그러면 이전 단계에서 빌드하고 배포한 Executor의 이미지로 Docker 컨테이너가 시작됩니다. 따라서 올바른 ID로 변경하는 것을 잊지 마세요. 

```python
uses_with={                                         # RequestLogger arguments
            'default_log_docs': 3
        },
```

필요한 인자를 전달하려면 `uses_with=` 가 필요합니다. 우리의 경우, 한 가지 인자만 있습니다: `default_log_docs`. `RequestLogger` Executor의 생성자에서 우리는 `default_log_docs` 를 `1` 로 정의했지만, 여기서는 `3` 으로 재정의하므로 `3` 이 새로운 값이 될 것입니다. 

다음 줄은 작업 공간을 나타냅니다:

```python
volumes='workspace:/internal_workspace',
```
앱을 실행할 때 생성되는 `workspace` 폴더를 Docker에 있는 `internal_workspace` 폴더와 맵핑합니다. 우리는 Executor가 문서를 파일에 기록하고, 해당 파일을 로컬 디스크에 저장하길 원하므로 이 작업을 수행합니다. 만약 이 작업을 하지 않는다면, 정보는 Docker 컨테이너에 저장될 것이고 파일을 보려면 해당 컨테이너에 엑세스해야 합니다. 이를 위해 `volumes=` 를 우리의 내부 작업 공간으로 설정합니다.

마지막 부분에서도 인자를 재정의하지만, 이번에는 `Executor` 의 부모 클래스에 대해 다음을 수행합니다:

```python
uses_metas={                                                # Executor (parent class) arguments
            'workspace': '/internal_workspace',             # this should match the above
        },
```

우리의 경우, 재정의하려는 인자는 `workspace` 의 이름입니다. 이렇게 하지 않으면 당신의 Executor 클래스(`RequestLogger`)와 동일한 이름의 폴더가 생성될 것이고, 그곳에 정보가 저장될 것입니다. 하지만 우리는 Docker에 `internal_workspace` 라는 이름을 가진 워크스페이스를 조직했기 때문에 같은 이름을 가진 폴더를 만들면 됩니다.

좋습니다. 우리는 이전에 배포한 Executor와 함께 `Flow` 가 준비되었습니다. 이제 이것을 사용할 수 있습니다. 문서를 인덱싱하여 시작해봅시다:

```python
with flow as f:                                                 # Flow is a context manager
        f.post(
            on='/index',                                        # the endpoint
            inputs=docs,                                        # the documents we send as input
        )
```

우리가 생성한 Executor는 엔드포인트에 무엇이 쓰였는지 신경쓰지 않으므로, 여기서 어떤 엔드포인트로 설정하든 동일한 작업을 수행할 것입니다. 이 예시에서는 `on='/index'` 로 설정했습니다. 필요한 경우 `index` 용 하나와 `query` 용 하나를 사용할 수 있고, 당신의 Executor는 적절한 엔드포인트를 가집니다. 

지금까지의 코드는 다음과 같아야 합니다:

```python
from jina import Flow, DocumentArray, Document


def main():
    docs = DocumentArray()
    docs.append(Document(content='I love cats'))                # creating documents
    docs.append(Document(content='I love every type of cat'))
    docs.append(Document(content='I guess dogs are ok'))

    flow = Flow().add(                                          # provide as class name or jinahub+docker URI
        uses='jinahub+docker://7dne55rj',
        uses_with={                                             # RequestLogger arguments
            'default_log_docs': 3
        },
        volumes='workspace:/internal_workspace',                # mapping local folders to docker instance folders
        uses_metas={                                            # Executor (parent class) arguments
            'workspace': '/internal_workspace',                 # this should match the above
        },
    )

    with flow as f:                                             # Flow is a context manager
        f.post(
            on='/index',                                        # the endpoint
            inputs=docs,                                        # the documents we send as input
        )


if __name__ == '__main__':
    main()
```

이것을 실행하면 내부에 두 개의 다른 폴더를 포함한 새로운 `workspace` 가  생성될 것입니다. 하나는 `RequestLogger` 나 당신이 클래스에서 이용한 이름일 것입니다. 그리고 sharding(분산 저장 관리)을 위한 또 다른 폴더가 있지만, 범위를 벗어나기 때문에 튜토리얼에서는 이야기하지 않겠습니다. `0` 이라는 sharding 폴더 안에 `log.txt` 이라는 파일이 있습니다. 그리고 그들의 정보가 포함된 3개의 문서가 있을 것입니다.

```{figure} ../../.github/images/log.png
:align: center
```

이게 끝입니다! 당신은 Executor를 만들었고, Jina Hub에 푸시했으며, 앱에서 사용했습니다.

아직 배워야할 개념이 많습니다. 우리의 튜토리얼을 계속 따라와주세요.

만약 이 튜토리얼을 수행하는 과정에서 문제가 생긴다면, 당신은 언제나 우리의 [Slack community](https://slack.jina.ai/)에서 도움을 받을 수 있습니다.

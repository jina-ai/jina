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

Jina 설치에 대한 자세한 내용은 [ref](https://github.com/jina-ai/jina/blob/master/docs/get-started/install.md#install) `페이지의 <install>`을 참조하세요.

## 나의 Executor 만들기

당신의 Executor를 만들려면 터미널에서 다음 명령어를 실행하기만 하면 됩니다: 

```shell
jina hub new
```

Wizard가 당신에게 Executor에 대해 몇 가지 질문을 할 것입니다. 기본 설정의 경우, 두 가지 질문이 표시됩니다:  

- Executor의 이름 
- 저장되어야 할 곳
 
이 튜토리얼의 경우, 우리는 **RequestLogger**라고 부르겠습니다. 그리고 당신은 이 프로젝트를 당신이 원하는 곳에 저장할 수 있습니다. Wizard는 고급 설정을 원하는지 물어볼 것이지만, 이 튜토리얼에서는 필요하지 않습니다.

### Logger Executor

Wizard를 따라 가면 폴더 구조가 준비됩니다. 우리는 `executor.py`파일을 가지고 시작할 수 있습니다. 해당 파일을 열고, 다음을 import합니다.

```python
import os
import time
from typing import Dict

from jina import Executor, DocumentArray, requests
from jina.logging.logger import JinaLogger
```

Then we create our class that inherits from the `Executor` base class. We will call ours `RequestLogger`

```{admonition} Important
:class: important
 
You always need to inherit from the `Executor` class, in order for the class to be properly registered into Jina.
```

```python
class RequestLogger(Executor):
```

Our Executor will have two methods: one for the constructor and one for the actual logging:

```python
class RequestLogger(Executor):    
    def __init__(self, **args, **kwargs):
        # Whatever you need for our constructor

    def log():
        # Whatever we need for our logging
```

It could be helpful to specify the number of Documents we want to work with, so we pass this directly in the arguments of our constructor

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

Now we start creating our constructor method. We set the `default_log_docs` we got from the arguments:

```python
self.default_log_docs = default_log_docs
```

For logging, we need to create an instance of `JinaLogger`. We also need to specify the path where we save our log file. 

```python
self.logger = JinaLogger('req_logger')
self.log_path = os.path.join(self.workspace, 'log.txt')
```

```{admonition} Note
:class: note

`self.workspace` will be provided by the `Executor` parent class.
```

And finally, we need to create the file, in case it doesn't exist.

```python
if not os.path.exists(self.log_path):
    with open(self.log_path, 'w'): pass
```

Ok, that's it for our constructor, by now we should have something like this:

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

We can start creating our `log` method now. First of all, we need the `@requests` decorator. This is to communicate to the `Flow` when the function will be called and on which endpoint. We use `@requests` without any endpoint, so we will call our function on every request:

```python
@requests
def log(self, 
        docs: Optional[DocumentArray],
        parameters: Dict,
        **kwargs):
```

It's important to note the arguments here. 

```{admonition} Important
:class: important

It's not possible to redefine the interface of the public methods decorated by `@requests`. You can't change the name of these arguments. To see exactly which parameters you can use, check {ref}`here <executor-method-signature>`.
```

If you would like to call your `log` function only on `/index` time, you specify the endpoint with `on=`, like this:

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

If you want more information on how to use this decorator, refer to {ref}`the documentation <executor-request-parameters>`. In this example, we want to call our `log` function on every request, so we don't specify any endpoint. 

Now we can add the logic for our function. First, we will print a line that displays some information. And then, we will save the details from our Documents:

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

Here you can set whatever logic you need for your Executor. By now, your code should look like this:

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

And that's it. We have an `Executor` that takes whatever Documents we pass to it and logs them. 

Ok, and what now? How can you use this in your app?

### Push your Executor to Hub

We could use our Executor directly in our app, but here we will see how to push it to Jina Hub so we can share it with more people, or use it later. 

First step is to actually make sure the `manifest.yml` and `config.yml` files are still relevant. Check that the data in there still represent you Executor's purpose.

For this, you need to open a terminal in the folder of your `executor.py`, so in this case, open a terminal inside the `RequestLogger` folder. And there you just need to type:

```bash
jina hub push --public .
```

This means you will push your Executor publicly to Jina Hub. The last dot means you will use your current path. Once you run that command, you should see something like this:

```{figure} ../../.github/images/push-executor.png
:align: center
```

```{admonition} Note
:class: note

Since we pushed our Executor using the `--public` flag, the only thing we will use is the ID. In this case, it's `zsor7fe6`. Refer to {ref}`Jina Hub usage <jina-hub-usage>`.
```

### Use your Executor

Let's create a Jina Flow that can use the Executor we just wrote.
Create an `app.py` in the same folder as `RequestLogger`. Now open it and import `Flow`, `DocumentArray`, `Document` before we create our `main function:

```python
from jina import Flow, DocumentArray, Document

def main():
    # We'll have our Flow here

if __name__ == '__main__':
    main()
```

The Executor we just created logs whatever Documents we pass to it. So we need to create some Documents first. We'll do that in `main()`

```python
def main():
    docs = DocumentArray()
    docs.append(Document(content='I love cats'))                # creating documents
    docs.append(Document(content='I love every type of cat'))
    docs.append(Document(content='I guess dogs are ok'))
```

We have three Documents in one `DocumentArray`. Now let's create a `Flow` and add the Executor we created. We will reference it by the ID we got when we pushed it (in my case, it was `zsor7fe6`):

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

This seems like plenty of details, so let's explain them:

```python
uses='jinahub+docker://zsor7fe6',
```

Here you use `uses=` to specify the image of your Executor. This will start a Docker container with the image of the Executor we built and deployed in the previous step. So don't forget to change the ID to the correct one.

```python
uses_with={                                         # RequestLogger arguments
            'default_log_docs': 3
        },
```

We need `uses_with=` to pass the arguments we need. In our case, we have only one argument: `default_log_docs`. In the constructor of our `RequestLogger` Executor, we defined the `default_log_docs` as `1`, but we override it here with `3`, so `3` will be the new value. 

The next line refers to our workspace:

```python
volumes='workspace:/internal_workspace',
```
Here we are mapping the `workspace` folder that will be created when we run our app to a folder called `internal_workspace` in Docker. We do this because our Executor logs the Documents into a file, and we want to save that file on our local disk. If we don't do that, the information would be saved in the Docker container, and you would need to access that container to see files.  To do this, we use `volumes=` and set it to our internal workspace. 

The last part overrides arguments too, but this time for the `Executor` parent class:

```python
uses_metas={                                                # Executor (parent class) arguments
            'workspace': '/internal_workspace',             # this should match the above
        },
```

In our case, the only argument we want to override is the name of the `workspace`. If you don't do this, a folder with the same name of your Executor class (`RequestLogger`) would be created, and your information would have been saved there. But since we just mounted our workspace with the name `internal_workspace` in Docker, we need to make a folder with that same name.

Ok, we have our `Flow` ready with the Executor we deployed previously. We can use it now. Let's start by indexing the Documents:

```python
with flow as f:                                                 # Flow is a context manager
        f.post(
            on='/index',                                        # the endpoint
            inputs=docs,                                        # the documents we send as input
        )
```

The Executor we created doesn't care about what endpoint is used, so it will perform the same operation no matter what endpoint you specify here. In this example, we set it to `on='/index'` anyway. Here you could use one for `index` and another one for `query` if you need it and your Executor has the proper endpoints. 

So far, your code should look like this:

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

When you run this, you will see a new `workspace` folder created with two other folders inside. One called `RequestLogger` or whatever name you used in your class. And another folder for the sharding, but we won't talk about that in this tutorial because it's out of scope. Inside the sharding folder called `0`, you will see a `log.txt` file. And there you will have the 3 Documents with their information.

```{figure} ../../.github/images/log.png
:align: center
```

And that's it! You created an Executor, pushed it to Jina Hub, and used it in your app.

There are still a lot of concepts to learn. So stay tuned for our following tutorials.

If you have any issues following this tutorial, you can always get support from our [Slack community](https://slack.jina.ai/)

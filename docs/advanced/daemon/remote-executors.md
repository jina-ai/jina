# Remote Executor

JinaD enables deploying Executors on remote machines. We can pass the remote info using `host`and `port_jinad` arguments in the Flow syntax. Here are a few examples of using remote Executors.


## Executor defined in YAML

````{tab} Local
```{code-block} python

from jina import Flow

f = Flow().add(uses='executor.yml',
               py_modules=['executor.py'])

```
````

````{tab} Remote
```{code-block} python
---
emphasize-lines: 3, 4
---
from jina import Flow

f = Flow().add(uses='executor.yml',
               host='1.2.3.4',
               port_jinad=8000,
               py_modules=['executor.py'])
```
````

## Executor from Hub

````{tab} Local
```{code-block} python
from jina import Flow

f = Flow().add(uses='jinahub+docker://AdvancedExecutor')

```
````

````{tab} Remote
```{code-block} python
---
emphasize-lines: 3, 4
---
from jina import Flow

f = Flow().add(uses='jinahub+docker://AdvancedExecutor',
               host='1.2.3.4',
               port_jinad=8000)

```
````

## Executors on different hosts

````{tab} Local
```{code-block} python

from jina import Flow

f = (Flow()
    .add(name=’encoder’,
         uses='encoder.yml',
         py_modules=['encoder.py'])
    .add(name=’indexer’,
         uses='indexer.yml',
         py_modules=[‘indexer.py'])
    )

```
````

````{tab} Remote
```{code-block} python
---
emphasize-lines: 4,5,9,10
---

f = (Flow()
    .add(name=’encoder’,
         uses='encoder.yml',
         host='1.2.3.4'
         port_jinad=8000,
         py_modules=['encoder.py'])
    .add(name=’indexer’,
         uses='indexer.yml',
         host='2.3.4.5',
         port_jinad=8000,
         py_modules=[‘indexer.py'])
    )

```
````

## Executor using class

````{tab} Local
```{code-block} python
from jina import Flow, Executor, requests

class MyAwesomeExecutor(Executor):
    @requests
    def foo(*args, **kwargs):
        ...

f = Flow().add(uses=MyAwesomeExecutor)

```
````

````{tab} Remote
```{code-block} python
---
emphasize-lines: 9,10,11
---
from jina import Flow, Executor, requests

class MyAwesomeExecutor(Executor):
    @requests
    def foo(*args, **kwargs):
        ...

f = Flow().add(uses=MyAwesomeExecutor,
               host='1.2.3.4',
               port_jinad=8000,
               py_modules=['path/to/this/file.py'])

```
````


## Executor using class + pip dependency

````{tab} Local
```{code-block} python
---
emphasize-lines: 6
---
from jina import Flow, Executor, requests

class TFExecutor(Executor):
    @requests
    def foo(*args, **kwargs):
        import tensorflow
        ...

f = Flow().add(uses=TFExecutor)

```
````

````{tab} Remote

```bash
# requirements.txt
tensorflow==2.4.0
```

```{code-block} python
---
emphasize-lines: 6, 10, 11, 13
---
from jina import Flow, Executor, requests

class TFExecutor(Executor):
    @requests
    def foo(*args, **kwargs):
        import tensorflow
        ...

f = Flow().add(uses=TFExecutor,
               host='1.2.3.4',
               port_jinad=8000,
               py_modules=['path/to/this/file.py'],
               upload_files=['requirements.txt'])

```
````

```{caution}
[Directory structure for Executors](../../fundamentals/executor/repository-structure) is not supported in JinaD yet.
```

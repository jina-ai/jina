(reload-executor)=
## Hot Reload

While developing your Executor, it can be useful to have the Executor be refreshed from the source code while you are working on it, without needing to restart the Flow server.

For this you can use the `reload` argument for the Executor so that it watches changes in the source code and the Executor YAML configuration file and makes sure that the changes are applied to the served Executor.

The Executor will keep track in changes inside the Executor source file, the Executor YAML configuration file, every file passed in `py_modules` argument from {meth}`~jina.Flow.add` and all the Python files inside the folder where the Executor class is defined and its sub-folders.

````{admonition} Caution
:class: caution
This feature is thought to let the developer iterate faster while developing or improving the Executor, but is not intended to be used in production environment.
````

````{admonition} Note
:class: note
This feature requires watchfiles>=0.18 package to be installed.
````

To see how this would work, let's have an Executor defined in a file `my_executor.py`
```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from the first version of MyExecutor'
```

We build a Flow and expose it:

```python
import os
from jina import Flow

from my_executor import MyExecutor

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


f = Flow(port=12345).add(uses=MyExecutor, reload=True)

with f:
    f.block()
```

We can see that the Executor is successfuly serving:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
I am coming from the first version of MyExecutor
```

We can edit the executor file and save the changes:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from a new version of MyExecutor'
```

You should see in the logs of the serving Executor 

```text
INFO   executor0/rep-0@11606 detected changes in: ['XXX/XXX/XXX/my_executor.py']. Refreshing the Executor                                                             
```

And after this, Executor will start serving with the renewed code.

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
'I am coming from a new version of MyExecutor'
```

Reloading will also be applied in case the Executor's YAML configuration file is changed. In this case, the Executor 
deployment restarts.

To see how this works, let's define an Executor configuration in `executor.yml`.
```yaml
jtype: MyExecutorBeforeReload
```

Build a Flow with the Executor in it and expose it:

```python
import os
from jina import Flow, Executor, requests

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


class MyExecutorBeforeReload(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorBeforeReload'


class MyExecutorAfterReload(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorAfterReload'


f = Flow(port=12345).add(uses='executor.yml', reload=True)

with f:
    f.block()
```

You can see that the Executor is running and serving:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
MyExecutorBeforeReload
```

You can edit the Executor YAML file and save the changes:

```yaml
jtype: MyExecutorAfterReload
```

In the Flow's logs we should see:

```text
INFO   Flow@1843 change in Executor configuration YAML /home/joan/jina/jina/exec.yml observed, restarting Executor deployment  
```

And after this, you can see the reloaded Executor being served:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```yaml
jtype: MyExecutorAfterReload
```

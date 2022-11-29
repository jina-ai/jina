(reload-executor)=
# Reload Executor

While developing your Executor, it can be useful to have the Executor be refreshed from the source code while you are working on it, without needing to restart the complete server.

For this you can use the `reload` argument for the Executor so that it watches changes in the source code and makes sure that the changes are applied live to the served Executor.

The Executor will keep track in changes inside the Executor source file, every file passed in `py_modules` argument from {meth}`~jina.Flow.add` and all the Python files inside the folder where the Executor class is defined and its subfolders.

````{admonition} Note
:class: note
This feature is thought to let the developer iterate faster while developing or improving the Executor, but is not intended to be used in production environment.
````

````{admonition} Note
:class: note
This feature requires watchfiles>=0.18 package to be installed.
````

To see how this would work, let's define an Executor in the file `my_executor.py`
```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from the first version of MyExecutor'
```

Then we build a Flow and expose it:

```python
import os
from jina import Flow

from my_executor import MyExecutor
os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


f = Flow(port=12345).add(uses=MyExecutor, reload=True)

with f:
    f.block()
```

Then we can see that the Executor is successfuly serving:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
I am coming from the first version of MyExecutor
```

Then we can edit `my_executor.py` and save the changes:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'I am coming from a new version of MyExecutor'
```

You should see in the logs of the serving Executor:

```text
INFO   executor0/rep-0@11606 detected changes in: ['XXX/XXX/XXX/my_executor.py']. Refreshing the Executor                                                             
```

After this, Executor will start serving with the renewed code.

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
'I am coming from a new version of MyExecutor'
```


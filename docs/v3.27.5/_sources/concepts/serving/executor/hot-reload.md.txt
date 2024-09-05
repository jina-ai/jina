(reload-executor)=
## Hot Reload

While developing your Executor, it can be useful to have the Executor be refreshed from the source code while you are working on it.

For this you can use the Executor's `reload` argument to watch changes in the source code and the Executor YAML configuration and ensure changes are applied to the served Executor.

The Executor will keep track of changes inside the Executor source and YAML files and all Python files in the Executor's folder and sub-folders).

````{admonition} Caution
:class: caution
This feature aims to let developers iterate faster while developing or improving the Executor, but is not intended to be used in production environment.
````

````{admonition} Note
:class: note
This feature requires watchfiles>=0.18 package to be installed.
````

To see how this would work, let's define an Executor in `my_executor.py`
```python
from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = 'I am coming from the first version of MyExecutor'
```

Now we'll deploy it

```python
import os
from jina import Deployment

from my_executor import MyExecutor

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


dep = Deployment(port=12345, uses=MyExecutor, reload=True)

with dep:
    dep.block()
```

We can see that the Executor is successfully serving:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
I come from the first version of MyExecutor
```

We can edit the Executor file and save the changes:

```python
from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = 'I am coming from a new version of MyExecutor'
```

You should see in the logs of the serving Executor 

```text
INFO   executor0/rep-0@11606 detected changes in: ['XXX/XXX/XXX/my_executor.py']. Refreshing the Executor                                                             
```

And after this, the Executor will start serving with the renewed code.

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
'I come from a new version of MyExecutor'
```

Reloading is also applied when the Executor's YAML configuration file is changed. In this case, the Executor deployment restarts.

To see how this works, let's define an Executor configuration in `executor.yml`:

```yaml
jtype: MyExecutorBeforeReload
```

Deploy the Executor:

```python
import os
from jina import Deployment, Executor, requests
from docarray import DocList
from docarray.documents import TextDoc

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


class MyExecutorBeforeReload(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = 'MyExecutorBeforeReload'


class MyExecutorAfterReload(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = 'MyExecutorAfterReload'


dep = Deployment(port=12345, uses='executor.yml', reload=True)

with dep:
    dep.block()
```

You can see that the Executor is running and serving:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
MyExecutorBeforeReload
```

You can edit the Executor YAML file and save the changes:

```yaml
jtype: MyExecutorAfterReload
```

In the Flow's logs you should see:

```text
INFO   Flow@1843 change in Executor configuration YAML /home/user/jina/jina/exec.yml observed, restarting Executor deployment  
```

And after this, you can see the reloaded Executor being served:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```yaml
jtype: MyExecutorAfterReload
```

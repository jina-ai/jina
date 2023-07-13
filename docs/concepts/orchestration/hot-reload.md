# Hot Reload

While developing your Orchestration, you may want it to reload automatically as you change the YAML configuration.

For this you can use the Orchestration's `reload` argument to reload it with the updated configuration every time you change the YAML configuration.

````{admonition} Caution
:class: caution
This feature aims to let developers iterate faster while developing, but is not intended for production use.
````

````{admonition} Note
:class: note
This feature requires `watchfiles>=0.18` to be installed.
````

````{tab} Deployment
To see how this works, let's define a Deployment in `deployment.yml` with a `reload` option:
```yaml
jtype: Deployment
uses: ConcatenateTextExecutor
uses_with:
  text_to_concat: foo
with:
  port: 12345
  reload: True
```

Load and expose the Orchestration:

```python
import os
from jina import Deployment, Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class ConcatenateTextExecutor(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text += text_to_concat
        return docs


os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


dep = Deployment.load_config('deployment.yml')

with dep:
    dep.block()
```

You can see that the Orchestration is running and serving:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
foo
```

You can edit the Orchestration YAML file and save the changes:

```yaml
jtype: Deployment
uses: ConcatenateTextExecutor
uses_with:
  text_to_concat: bar
with:
  port: 12345
  reload: True
```

You should see the following in the Orchestration's logs:

```text
INFO   Deployment@28301 change in Deployment YAML deployment.yml observed, restarting Deployment                                                   
```

After this, the behavior of the Deployment's Executor will change:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
bar
```
````

````{tab} Flow
To see how this works, let's define a Flow in `flow.yml` with a `reload` option:
```yaml
jtype: Flow
with:
  port: 12345
  reload: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
```

Load and expose the Orchestration:

```python
import os
from jina import Deployment, Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class ConcatenateTextExecutor(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text += text_to_concat
        return docs


os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


f = Flow.load_config('flow.yml')

with f:
    f.block()
```

You can see that the Flow is running and serving:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
add text
```

You can edit the Flow YAML file and save the changes:

```yaml
jtype: Flow
with:
  port: 12345
  reload: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
- name: exec2
  uses: ConcatenateTextExecutor
```

You should see the following in the Flow's logs:

```text
INFO   Flow@28301 change in Flow YAML flow.yml observed, restarting Flow                                                   
```

After this, the Flow will have two Executors with the new topology:

```python
from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

c = Client(port=12345)

print(c.post(on='/', inputs=DocList[TextDoc](TextDoc()), return_type=DocList[TextDoc])[0].text)
```

```text
add text add text
```

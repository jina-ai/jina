(restart-flow)=
# Hot Reload

While developing your Flow, it can be useful to have it restart automatically as you change the Flow YAML.

For this you can use the Flow's `restart` argument to restart it with the updated configuration every time you change the YAML configuration.

````{admonition} Caution
:class: caution
This feature aims to let developers iterate faster while developing, but is not intended for production use.
````

````{admonition} Note
:class: note
This feature requires watchfiles>=0.18 package to be installed.
````

To see how this works, let's define a Flow in `flow.yml` with a restart option.
```yaml
jtype: Flow
with:
  port: 12345
  restart: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
```

We build a Flow and expose it:

```python
import os
from jina import Flow, Executor, requests


class ConcatenateTextExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text += 'add text '


os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


f = Flow.load_config('flow.yml')

with f:
    f.block()
```

We can see that the Flow is running and serving:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
add text
```

We can edit the Flow YAML file and save the changes:

```yaml
jtype: Flow
with:
  port: 12345
  restart: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
- name: exec2
  uses: ConcatenateTextExecutor
```

You should see the following in the Flow's logs:

```text
INFO   Flow@28301 change in Flow YAML XXX/flow.yml observed, restarting Flow                                                   
```

After this, the Flow will have two Executors with the new topology:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
add text add text
```

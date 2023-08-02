(python-yaml)=
# Coding in Python/YAML

In the docs, you often see two coding styles when describing a Jina project: 

```{glossary}

**Pythonic**
    Flows, Deployments and Executors are all written in Python files, and the entrypoint is via Python.
    
**YAMLish**
    Executors are written in Python files, and the Flow or Deployment are defined in a YAML file. The entrypoint is via Jina CLI `jina flow --uses flow.yml`.
```

For example, {ref}`the server-side code<dummy-example>` above follows {term}`Pythonic` style. It can be written in {term}`YAMLish` style as follows:

````{tab} executor.py
```python
from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class FooExec(Executor):
    @requests
    async def add_text(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for d in docs:
            d.text += 'hello, world!'


class BarExec(Executor):
    @requests
    async def add_text(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for d in docs:
            d.text += 'goodbye!'
```
````

````{tab} flow.yml
```yaml
jtype: Flow
with:
  port: 12345
executors:
- uses: FooExec
  replicas: 3
  py_modules: executor.py
- uses: BarExec
  replicas: 2
  py_modules: executor.py
```
````

````{tab} Entrypoint
```bash
jina flow --uses flow.yml
```
````

In general, the YAML style can be used to represent and configure a Flow or Deployment which are the objects orchestrating the serving of Executors and applications.
The YAMLish style separates the Flow or Deployment representation from the logic code from Executors. It is more flexible to configure and should be used for more complex projects in production. In many integrations such as JCloud and Kubernetes, YAMLish is preferred. 

Note that the two coding styles can be converted to each other easily. To load a Flow YAML into Python and run it:

```python
from jina import Flow

f = Flow.load_config('flow.yml')

with f:
    f.block()
```

To dump a Flow into YAML:

```python
from jina import Flow

Flow().add(uses=FooExec, replicas=3).add(uses=BarExec, replicas=2).save_config(
    'flow.yml'
)
```

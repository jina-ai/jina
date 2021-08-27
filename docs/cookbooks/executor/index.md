# Executor

Executor represents a processing component in a Jina Flow. It performs a single task on a `Document` or 
`DocumentArray`. Executors can fall into different categories:

- Segmenter
- Crafter
- Encoder
- Indexer
- Ranker

You can create an Executor by extending the {class}`Executor` class and adding logic to endpoint methods.

## Minimum working example

### Pure Python

```python
from jina import Executor, Flow, Document, requests


class MyExecutor(Executor):

    @requests
    def foo(self, **kwargs):
        print(kwargs)


f = Flow().add(uses=MyExecutor)

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
```

### With YAML

`MyExecutor` described as above. Save it as `foo.py`.

`my.yml`:

```yaml
jtype: MyExecutor
metas:
  py_modules:
    - foo.py
  name: awesomeness
  description: my first awesome executor
requests:
  /random_work: foo
```

In this example your executor is defined in a single python file, `foo.py`. If you want to use multiple python files
(for example, `foo.py` and `helper.py`), check out how to organize them in the section [Structure of the Repository](#structure-of-the-repository)

Construct `Executor` from YAML:

```python
from jina import Executor

my_exec = Executor.load_config('my.yml')
```

Flow uses `Executor` from YAML:

```python
from jina import Flow, Document

f = Flow().add(uses='my.yml')

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
```

```{toctree}
:hidden:

executor-api
executor-built-in-features
executors-in-action
repository-structure
```

(executor-cookbook)=
# Executor

Executor represents a processing component in a Jina Flow. It performs a single task on a `Document` or 
`DocumentArray`. 

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
(for example, `foo.py` and `helper.py`), check out how to organize them in the section 
{ref}`Structure of the Repository<structure-of-the-repository>`

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

````{admonition} See Also
:class: seealso
{ref}`Flow <flow-cookbook>`
````

```{toctree}
:hidden:

executor-api
executor-built-in-features
executors-in-action
repository-structure
```

#### Design Principle of Executor

In Jina 2.0 the Executor class is generic to all categories of executors (`encoders`, `indexers`, `segmenters`,...) to
keep development simple. We do not provide subclasses of `Executor` that are specific to each category. The design
principles are (`user` here means "Executor developer"):

- **Do not surprise the user**: keep `Executor` class as Pythonic as possible. It should be as light and unintrusive as
  a `mixin` class:
    - do not customize the class constructor logic;
    - do not change its built-in interfaces `__getstate__`, `__setstate__`;
    - do not add new members to the `Executor` object unless needed.
- **Do not overpromise to the user**: do not promise features that we can hardly deliver. Trying to control the
  interface while delivering just loosely-implemented features is bad for scaling the core framework. For
  example, `save`, `load`, `on_gpu`, etc.

We want to give our users the freedom to customize their executors easily. If a user is a good Python programmer, they
should pick up `Executor` in no time. It is as simple as subclassing `Executor` and adding an endpoint.

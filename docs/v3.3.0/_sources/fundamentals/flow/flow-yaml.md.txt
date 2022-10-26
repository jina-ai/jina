# Configure a Flow from YAML

Instead of constructing a Flow in Python source codes, using a YAML file is the recommended way to configure Flows 
because it is 

- independent of the Python source codes,
- easy to edit, maintain and extend,
- human-readable.

## Load and Save a Flow configuration
`load_config()` is used to load the Flow configuration from a YAML file. Correspondingly, one uses `save_config()`  to 
save the Flow configuration. In the following example, `jtype: Flow` in the YAML file tells the parser to construct a 
`Flow` using this YAML file. 

`flow.yml`:

```yaml
jtype: Flow
```

```python
from jina import Flow

f = Flow.load_config('flow.yml')  # Load the Flow definition from Yaml file
...
f.save_config('flow.yml')
```

## Configure Executors
`executors` field in the YAML file is for adding Executors to the Flow. It accepts a list of dictionaries, each of 
which specifies a configuration of one executor. The dictionary accepts all the arguments from the `add()` method of the 
Flow. 
`uses` field is used to define the type of the Executor. As for using a local executor with source codes, the grammar 
for setting `uses` is the same as that for configuring Executors in a YAML file. As for the other sources, one can 
assign strings directly, for example `jinahub+sandbox://Hello`. 

`flow.yml`:

```yaml
jtype: Flow
executors:
  - name: local_executor_with_source_codes
    uses: 
      jtype: LocalExecutor
      metas:
        py_modules:
          - executors.py
      with:
        foo: 'Foo'
  - name: sandbox_executor
    uses: 'jinahub+sandbox://Hello'
```

`executors.py`:

```python
from jina import Executor, requests


class LocalExecutor(Executor):
    def __init__(self, foo, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo

    @requests
    def foo(self, **kwargs):
        print(f'foo={self.foo}')
```

## Configure Flow APIs
Use `with` field to configure the Flow APIs. It accepts all the arguments in Flow constructor. In the example below, we 
set the Flow to serve `http` at the port `45678` with CORS being enabled.

```yaml
jtype: Flow
with:
  port: 45678
  protocol: 'http'
  cors: True
```

## Configure Flow Meta Information
In the case that you want to set the same value for the `metas` attributes in **all** the executors, `metas` field can 
help. This is very helpful when you use the executors with local source codes and have all of them in one Python module.
In the following example, the two executors are defined in the same module.

````{tab} Use Flow metas

```yaml
jtype: Flow
metas:
  py_modules:
    - executors.py
executors:
  - uses: FooExecutor
  - uses: BarExecutor
```

````

````{tab} Use Executor metas

```yaml
jtype: Flow
executors:
  - uses:
      jtype: FooExecutor
      metas:
        py_modules:
          - executors.py
  - uses:
      jtype: BarExecutor
      metas:
        py_modules:
          - executors.py
```

````


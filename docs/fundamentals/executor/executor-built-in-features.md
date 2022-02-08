# Executor Features

## YAML interface

An Executor can be loaded from and stored to a YAML file. The YAML file has the following format:

```yaml
jtype: MyExecutor
with:
  parameter_1: foo
  parameter_2: bar
metas:
  name: MyExecutor
  description: "MyExecutor does a thing to the stuff in your Documents"
  workspace: workspace
  py_modules:
    - executor.py
requests:
  index: MyExecutor_index_method
  search: MyExecutor_search_method
  random: MyExecutor_other_method
```

- `jtype` is a string. Defines the class name, interchangeable with bang mark `!`;
- `with` is a map. Defines kwargs of the class `__init__` method
- `metas` is a dictionary. It defines the meta information of that class. It contains the following fields:
    - `name` is a string. Defines the name of the executor;
    - `description` is a string. Defines the description of this executor. It will be used in automatic docs UI;
    - `workspace` is a string. Defines the workspace of the executor;
    - `py_modules` is a list of strings. Defines the Python dependencies of the executor;
- `requests` is a map. Defines the mapping from endpoint to class method name. Useful if one needs to overwrite the default methods

## Meta attributes

By default, an `Executor` object contains two collections of attributes: `.metas` and `.runtime_args`. They are both
in `SimpleNamespace` type and contain some key-value information. However, they are defined differently and serve
different purposes.

- **`.metas` are statically defined.** "Static" means, e.g. from hard-coded value in the code, from a YAML file.
- **`.runtime_args` are dynamically determined during runtime.** Means that you don't know the value before running
  the `Executor`, e.g. `shard_id`, `replicas`. Those values are often related to the system/network
  environment around the `Executor`, and less about the `Executor` itself. They are usually set with the {meth}`~jina.flow.base.Flow.add` 
  method. See the list of options [here](https://docs.jina.ai/cli/#executor).

The following fields are valid for `metas` and `runtime_args`:

| Attribute                                                                                 | Fields                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.metas` (static values from hard-coded values, YAML config)                              | `name`, `description`, `py_modules`, `workspace`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `.runtime_args` (runtime values from its containers, e.g. `Runtime`, `Pod`, `Deployment`) | `name`, `workspace`, `shard_id`, `replicas`, 'shards' |


````{admonition} Note
:class: note
The YAML API will ignore `.runtime_args` during save and load as they are not statically stored
````

````{admonition} Hint
:class: hint
For any other parametrization of the Executor, you can still access its constructor arguments (defined in the
class `__init__`) and the request `parameters`
````

````{admonition} Note
:class: note
`workspace` will be retrieved from either `metas` or `runtime_args`, in that order
````


## Workspace

Executor's workspace is inherited according to the following rule (`OR` is a python `or`, i.e. first thing first, if NA
then second):

```{figure} ../../../.github/2.0/workspace-inherit.svg
:align: center
```



## Gracefully close Executor

You might need to execute some logic when your executor's destructor is called. For example, you want to
persist data to the disk (e.g. in-memory indexed data, fine-tuned model,...). To do so, you can overwrite the
method `close` and add your logic.

```{code-block} python
---
emphasize-lines: 11, 12
---
from jina import Executor, requests, Document, DocumentArray


class MyExec(Executor):

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(doc.text)

    def close(self):
        print("closing...")


with MyExec() as executor:
    executor.foo(DocumentArray([Document(text='hello world')]))
```

```text
hello world
closing...
```

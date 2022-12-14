(debug-executor)=
# Debug

````{admonition} Not applicable to Containerized Executor
:class: caution
This does not work for containerized Executors.
````

In this tutorial you will learn how to debug [Hello Executor](https://cloud.jina.ai/executor/9o9yjq1q) step by step.

## Pull the Executor

Pull the source code of the Executor you want to debug:

````{tab} via Command Line Interface
```shell
jina hub pull jinahub://Hello
```
````
````{tab} via Python code
```python
from jina import Executor

Executor.from_hub('jinahub://Hello')
```
````

## Set the breakpoints

In the `~/.jina/hub-package` directory there is one subdirectory for each Executor that you pulled, named by the Executor id. You can find the Executor's source files Executor in this directory.

Once you locate the source, you can set the breakpoints as you always do.

## Debug your code

You can debug your Executor like any Python code. You can either use the Executor on its own or inside a Flow:

````{tab} Executor on its own
```python
from jina import Executor

exec = Executor.from_hub('jinahub://Hello')

# Set breakpoint as needed
exec.foo()
```
````
````{tab} Executor inside a Flow
```python
from docarray import Document
from jina import Flow

f = Flow().add(uses='jinahub://Hello')

with f:
    res = f.post('/', inputs=Document(text='hello'), return_results=True)
    print(res)
```
````

(debug-executor)=
# How to debug an Executor

````{admonition} Caution
:class: caution
To debug an Executor, you need to look under the hood of Jina. This means things are not straightforward and might change in the future.
````

````{admonition} Containerized Executor
:class: danger
This How-To does not work for containerized Executors.
````

It's very easy to debug Jina Executors. In this How-To, you will learn how to debug [Hello Executor](https://hub.jina.ai/executor/9o9yjq1q) step by step.

## Step 1: Pull the Executor

Pull the source code of the Executor you want to debug. There are two ways to do that.

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

## Step 2: Set the Breakpoints

Go to `~/.jina/hub-package` directory. In this folder, there will be one subdirectory for each Executor that you pulled, named by the Executor id. You can find the source files of the Executor in this directory. 

Once you locate the source, you can set the breakpoints as you always do. 

## Step 3: Debug Your Code

Now you can debug your Executor like any Python code. You can either use the Executor on its own or use it inside a Flow.

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

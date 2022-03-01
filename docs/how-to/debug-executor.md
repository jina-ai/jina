(debug-executor)=
# How to Debug Executor

You need to debug Jina Hub Executor for some reason. It's not so easy to debug inside the Docker container, but Jina Hub Executor provides a way to use source code. It's easy to debug using source code. 

I'll take debugging [Hello Executor](https://hub.jina.ai/executor/9o9yjq1q) as an example. Tell you step by step how to do that. 

## Step 1

Prepare code snippet. 

```python
from docarray import Document
from jina import Flow, Executor

exec = Executor.from_hub('jinahub://Hello')

f = Flow().add(uses=type(exec))

with f:
    res = f.post('/', inputs=Document(text='hello'), return_results=True)
    print(res)
```

````{admonition} Important
:class: important
`type` is important as exec is an object, whereas .add(uses=) accept only class.
````

## Step 2

Open the Jina Hub Executor python file and set the debug point. The source code is located in `~/.jina/hub-package`.

## Step 3

Debugging.
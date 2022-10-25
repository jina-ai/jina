(flow-switch)=
# Conditional route request inside a Flow

This tutorial gives a deeper insight into the {class}`~jina.Flow`'s {ref}`filter condition feature<flow-filter>`.

In a nutshell, this lets any {class}`~jina.Executor` filter Documents that fulfill a specified `condition`, letting you build *selection control* into your Flow.

````{admonition} See Also
:class: seealso

If you're not familiar with the basics of the [DocArray query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions) and how it is used to create
{ref}`filters <flow-filter>`, read the linked documentation pages first.
````

## Why use selection control?

Jina Flows can define complex {ref}`topologies <flow-complex-topologies>` that include multiple Executors,
both in sequence and/or on parallel branches.

A simple Flow with parallel branches could be defined like so:

```python
from jina import Flow

f = (
    Flow()
    .add(name='start_exec')
    .add(name='exec1', needs='start_exec')
    .add(name='exec2', needs='start_exec')
    .needs_all()
)
f.plot()
```

```{figure} simple-parallel-flow.svg
:width: 70%
:align: center
Flow with two parallel branches.
```

This kind of topology means that Documents don't get processed by `exec1` before they go to `exec2`, and vice versa.
However, all Documents still go through all branches and all Executors.

Sometimes you may not want all Documents to be processed by all Executors, for example when you index Documents
representing different kinds of data, like text and images.

One way to achieve this is to use different Executor endpoints:

````{tab} Main app

```{code-block} python
---
emphasize-lines: 19, 23
---
from docarray import DocumentArray, Document
from jina import Flow
import numpy as np


f = (
    Flow()
    .add(name='start_exec')
    .add(name='ImageIndexer', uses=ImageIndexer, needs='start_exec')
    .add(name='TextIndexer', uses=TextIndexer, needs='start_exec')
    .needs_all()
)

text_data = DocumentArray([Document(text='hey there!') for _ in range(2)])
image_data = DocumentArray(
    [Document(tensor=np.random.rand(2, 2)) for _ in range(2)]
)  # dummy images
with f:
    embedded_texts = f.post(inputs=text_data, on='/index-text')
    print(embedded_texts[:, 'tags'])
    print(embedded_texts.embeddings)
    print('---------')
    embedded_images = f.post(inputs=image_data, on='/index-images')
    print(embedded_images[:, 'tags'])
    print(embedded_images.embeddings)
```
````

````{tab} Define Executors

```{code-block} python
---
emphasize-lines: 7, 15
---
from docarray import DocumentArray, Document
from jina import Executor, requests
import numpy as np


class TextIndexer(Executor):
    @requests(on='/index-text')
    def index(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.rand(len(docs), 3)  # dummy embeddings
        for doc in docs:
            doc.tags['embedded_by'] = 'textIndexer'


class ImageIndexer(Executor):
    @requests(on='/index-images')
    def index(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.rand(len(docs), 3)  # dummy embeddings
        for doc in docs:
            doc.tags['embedded_by'] = 'imageIndexer'
```
````

```shell
[{'embedded_by': 'textIndexer'}, {'embedded_by': 'textIndexer'}]
[[0.37511057 0.14902827 0.31666838]
 [0.18466062 0.17823904 0.20046065]]
---------
[{'embedded_by': 'imageIndexer'}, {'embedded_by': 'imageIndexer'}]
[[0.37511057 0.14902827 0.31666838]
 [0.18466062 0.17823904 0.20046065]]
```

As you can see, image data was only processed by `ImageIndexer`, and text data was only processed by `TextIndexer`.

However, there's a problem with this approach:
Sometimes you can't easily control the endpoints of all Executors, for example when you are using {ref}`Executor Hub <jina-hub>` or {ref}`external Executors <external-executor>`.

To solve this, filter conditions easily add selection control to your Flow.

## Define the filter conditions

You can use the [DocArray query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions) to specify a filter condition for each Executor.

To do this, pass a condition to the `when` parameter in `flow.add()`:

```python
from jina import Flow

f = Flow().add(when={'tags__key': {'$eq': 5}})
```

Then only Documents that satisfy the `when` condition will reach the associated Executor. Any Documents that don't satisfy that condition won't reach the Executor.

If you are trying to separate Documents according to the data modality they hold, you need to choose
a condition accordingly.

````{admonition} See Also
:class: seealso

In addition to `$exists` you can use a number of other operators to define your filter: `$eq`, `$gte`, `$lte`, `$size`,
`$and`, `$or` and many more. For details, consult this [DocArray documentation page](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).
````

```python
# define filter conditions
text_condition = {'text': {'$exists': True}}
tensor_condition = {'tensor': {'$exists': True}}
```

These conditions specify that only Documents that hold data of a specific modality can pass the filter.

### Try the filters outside the Flow

You can use conditions directly on your data, outside the Flow:

```python
filtered_text_data = data.find(text_condition)
filtered_image_data = data.find(tensor_condition)

print(filtered_text_data.texts)  # print text
print('---')
print(filtered_image_data.tensors)
```
```shell
['hey there!', 'hey there!']
---
[[[0.50535537 0.50538128]
  [0.40446746 0.34972967]]

 [[0.04222604 0.70102327]
  [0.12079661 0.65313938]]]
```

Each filter selects Documents that contain the desired data fields.
That's exactly what you want for your filter!

## Build the Flow

Finally, assemble your Flow using these conditions and the indexers from above.
This time you don't need to choose different Executor endpoints, since the filters take care of 
selection control logic.

````{tab} Flow

```{code-block} python
---
emphasize-lines: 10, 16
---
from jina import Flow

f = (
    Flow()
    .add(name='start_exec')
    .add(
        name='ImageIndexer',
        uses=ImageIndexer,
        needs='start_exec',
        when={'tensor': {'$exists': True}},
    )
    .add(
        name='TextIndexer',
        uses=TextIndexer,
        needs='start_exec',
        when={'text': {'$exists': True}},
    )
    .needs_all()
)
```
````

````{tab} Executors

```{code-block} python
---
emphasize-lines: 7, 15
---
from docarray import DocumentArray, Document
from jina import Executor, requests
import numpy as np


class TextIndexer(Executor):
    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.rand(len(docs), 3)  # dummy embeddings
        for doc in docs:
            doc.tags['embedded_by'] = 'textIndexer'


class ImageIndexer(Executor):
    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.rand(len(docs), 3)  # dummy embeddings
        for doc in docs:
            doc.tags['embedded_by'] = 'imageIndexer'
```
````

Here you tell each Executor to filter its inputs according to the conditions specified above:
Text and image data should be treated separately.

## Index the data

When you send your data to the Flow, you expect that only your image data will be sent to `ImageIndexer`, and only your
text data will be sent to `TextIndexer`.

Let's take a look:

```python
with f:
    embedded_docs = f.post(on='/index', inputs=data)

embedded_by = embedded_docs[:, 'tags__embedded_by']
texts = embedded_docs.texts
tensors = embedded_docs.tensors
for embedded_by, text, image in list(zip(embedded_by, texts, tensors)):
    print(f'Embedded by: {embedded_by}; Text: {text}, Image: {image}')
```

```shell
Embedded by: textIndexer; Text: hey there!, Image: None
Embedded by: textIndexer; Text: hey there!, Image: None
Embedded by: imageIndexer; Text: , Image: [[0.60863086 0.39863197], [0.78668579 0.66100752]]
Embedded by: imageIndexer; Text: , Image: [[0.78359225 0.75458748], [0.56896536 0.66725426]]
```

And indeed, that's exactly what happens!

The Documents that have a text were processed by `TextIndexer`, and the Documents that contain an image were processed by `ImageIndexer`.
And remember, with this solution the Documents don't even get *sent* to the incorrect Executor.

## What's next

Now that you know how to use filter conditions to add selection control, you can use this feature to build all kinds of business logic.

You could differentiate between more than just two different data modalities, direct requests based on the Client they come from,
ignore Documents that don't meet certain quality criteria, or route data to specialized Executors based on what the data
itself looks like. Your imagination is the limit!

## See also

- {ref}`How to run your Flow with Docker Compose <docker-compose>`
- {ref}`How to deploy your Flow on Kubernetes <kubernetes>`
- {ref}`How to scale Executors in your Flow <scale-out>`

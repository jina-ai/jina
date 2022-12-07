(flow-filter)=
# Add Conditioning

Sometimes you may not want all Documents to be processed by all Executors. For example when you process text and images Documents you want to forward them to different Executors, respectively. 

You can set a conditioning for every {class}`~jina.Executor` in the Flow. Documents that do not meet the condition will be removed before reaching that Executor. This allows you to build a selection control in the Flow.



## Define conditions

To add a condition to an Executor, pass it to the `when` parameter of {meth}`~jina.Flow.add` method of the Flow.
This then defines *when* a document is processed by the Executor:

You can use the [DocArray query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions) to specify a filter condition for each Executor.

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



````{tab} Python

```{code-block} python
---
emphasize-lines: 3, 8
---
from jina import Flow, DocumentArray, Document

f = Flow().add().add(when={'tags__key': {'$eq': 5}})  # Create the empty Flow, add condition

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```

````

````{tab} YAML

```yaml
jtype: Flow
executors:
  - name: executor
    when:
        tags__key:
            $eq: 5
```

```{code-block} python
---
emphasize-lines: 9
---
from docarray import DocumentArray, Document
from jina import Flow

f = Flow.load_config('flow.yml')  # Load the Flow definition from Yaml file

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```
````

Note that if a Document does not satisfy the `when` condition of a filter, the filter removes the Document *for the entire branch of the Flow*.
This means that every Executor located behind a filter is affected by this, not just the specific Executor that defines the condition.
As with a real-life filter, once something fails to pass through it, it no longer continues down the pipeline.

Naturally, parallel branches in a Flow do not affect each other. So if a Document gets filtered out in only one branch, it can
still be used in the other branch, and also after the branches are re-joined:

````{tab} Parallel Executors

```{code-block} python
---
emphasize-lines: 7, 8
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, needs='first', name='exec1')
    .add(when={'tags__key': {'$eq': 4}}, needs='first', name='exec2')
    .needs_all(name='join')
)
```

```{figure} conditional-flow.svg
:width: 70%
:align: center
```

```python
with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # Each Document satisfies one parallel branch/filter
```

```shell
[{'key': 5.0}, {'key': 4.0}]
```

````

````{tab} Sequential Executors
```{code-block} python
---
emphasize-lines: 7, 8
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, name='exec1', needs='first')
    .add(when={'tags__key': {'$eq': 4}}, needs='exec1', name='exec2')
)
```

```{figure} sequential-flow.svg
:width: 70%

```


```python
with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # No Document satisfies both sequential filters
```

```shell
[]
```
````

This feature is useful to prevent some specialized Executors from processing certain Documents.
It can also be used to build *switch-like nodes*, where some Documents pass through one branch of the Flow,
while other Documents pass through a different parallel branch.

Note that whenever a Document does not satisfy the condition of an Executor, it is not even sent to that Executor.
Instead, only a tailored Request without any payload is transferred.
This means that you can not only use this feature to build complex logic, but also to minimize your networking overhead.

## Try filtering outside the Flow

You can use conditions directly on the data, outside the Flow:

```python
da = ...  # type: docarray.DocumentArray
filtered_text_data = da.find(text_condition)
filtered_image_data = da.find(tensor_condition)

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

````{admonition} See Also
:class: seealso

For a hands-on example of leveraging filter conditions, see {ref}`this how-to <flow-switch>`.
````

To define a filter condition, use [DocArrays rich query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).

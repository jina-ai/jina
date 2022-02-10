# Migration to Jina 3

Jina 3 introduces a number of exciting features **TODO ADD LINK TO EXCITING FEATURES**, but to be able to enjoy them, you will also have to make some
tweaks to your existing Jina 2 code.

One of the major changes in Jina 3 is the inclusion of [DocArray](https://docarray.jina.ai/):
The previously included `Document` and `DocumentArray` data structures now form their own library and include new
features, improved performance, and increased flexibility.
Accordingly, the scope of the changes in Jina 3 will be mainly related to `Document` and `DocumentArray`.

```{admonition} DocArray library
:class: seealso
[DocArray](https://docarray.jina.ai/) is our new library that includes the `Document` and `DocumentArray` data
structures. Inside their own library, `Document` and `DocumentArray` are faster and more versatile than ever, and
underpin neural search apps as well as the Jina ecosystem, including [Jina](https://docs.jina.ai/) and
[Finetuner](https://finetuner.jina.ai/).
```

In general, the breaking changes are aiming for increased simplicity and consistency, making your life easier in the
long run. Here you can find out what exactly you will have to adapt.

## More natural attribute names

Docarray introduces more natural naming conventions for `Document` and `DocumentArray` attributes.

- `doc.blob` is renamed to `doc.tensor`, to align with external libraries like PyTorch and Tensorflow
- `doc.buffer` is renamed to `doc.blob`, to align with the industry standard

## Simplified access of attributes and elements

**Attributes**: Docarray introduces a flexible way of accessing attributes of `Document`s in a `DocuemntArray`, in bulk.
- Instead of having to call `docs.get_attributes('attribute')`, you can simply call `docs.attributes` for
  a select number of attributes. Currently, this syntax is supported by:
  - `text`: `docs.texts`
  - `blob`: `docs.blobs`
  - `tensor`: `docs.tensors`
  - `content`: `docs.contents`
  - `embedding`: `docs.embeddings`
- The remaining attributes can be accessed in bulk by calling `docs[:, 'attribute']`, e.g. `docs[:, 'tags']`.
  Additionally, you can access a specific key in `tags` by calling `docs[:'tags__key']`.

**Array Traversal**: For traversing `DocumentArray`s via a `traversal_path`, docarray introduces a simplified notation:

- Traversal paths of the form `[path1, path2]` (e.g. `['r', 'cm']`) are replaced by a single string of the form
`'path1,path2'` (e.g. `'r,cm'`)
- `docs.traverse_flat(path)` is replaced by `docs['@path']` (e.g. `docs['@r,cm']`)
- `docs.flatten()` is replaced by `docs[...]`

````{tab} Jina 2

```python
from Jina import Document, DocumentArray

docs = nested_docs()

print(docs.traverse_flat('r,c').texts)
>>> ['root1', 'rooot2', 'chunk11', 'chunk12', 'chunk21', 'chunk22']

print(docs.flatten().texts)
>>> ['chunk11', 'chunk12', 'root1', 'chunk21', 'chunk22', 'root2']

```

````

````{tab} Jina 3 

```python
from Jina import Document, DocumentArray

docs = nested_docs()

print(docs['@r,c'].texts)
>>> ['root1', 'rooot2', 'chunk11', 'chunk12', 'chunk21', 'chunk22']

print(docs[...].texts)
>>> ['chunk11', 'chunk12', 'root1', 'chunk21', 'chunk22', 'root2']

```

````

**Batching**: Batching operations are delegated to the docarray package and Python builtins:

- `docs.batch()` does not accept the arguments `traversal_paths=` and `require_attr=` anymore.
The example below shows how to achieve complex behavior that previously relied on these arguments, in a more pythonic
and Jina 3 compatible way:

````{tab} Jina 2

```python
docs.batch(traversal_paths=paths, batch_size=bs, require_attr='attr')
```

````

````{tab} Jina 3 

```python
DocumentArray(filter(lambda x : bool(x.attr), docs['@paths'])).batch(batch_size=bs)
```

````

## Method behavior changes

- **`.post()` method**: `flow.post()` now returns a flattened `DocumentArray` instead of a list of `Response`s, if `return_results=True` is
set. This makes it easier to immediately use the returned results. The behavior of `client.post()` remains unchanged
compared to Jina 2, exposing entire `Response`s to the user. By setting or unsetting the `results_as_docarray=` flag,
the user can override these default behaviors.
- **Accessing non-existent values**: In Jina 2, bulk accessing attributes in a `DocumentArray` returns a list of empty values, when the `Document`s
inside the `DocumentArray` do not have a value for that attribute. In Jina 3, this returns `None`. This change becomes
important when migrating code that checks for the presence of a certain attribute.

````{tab} Jina 2

```python
from Jina import Document, DocumentArray

d = Document()
print(d.text)
>>> ''

docs = DocumentArray([d, d])
print(docs.texts)
>>> ['', '']
```

````

````{tab} Jina 3 

```python
from Jina import Document, DocumentArray

d = Document()
print(d.text)
>>> ''

docs = DocumentArray([d, d])
print(docs.texts)
>>> None
```

````


## Pythonic serialization

- `doc.SerializeToString()` is removed in favour of `doc.to_bytes()`
- Creating a `Document` from serialized data using `Document(bytes)` is removed in favour of
`Document.from_bytes(bytes)`


## Consistent YAML parsing syntax

In Jina 3, YAML syntax is aligned with [Github Actions notation](https://docs.github.com/en/actions/learn-github-actions/environment-variables),
which leads to the following changes:

- Referencing *environment variables* using the syntax `${{ VAR }}` is no longer allowed. The POSIX notations for
environment variables, `$var`, has been deprecated. Instead, use `${{ ENV.VAR }}`.
- The syntax `${{ VAR }}` now defaults to signifying a *context variable*, passed in a `dict()`. If you want to be explicit
about the use of context variables, you can use `${{ CONTEXT.VAR }}`.
- *Relative paths* can point to other variables within the same `.yaml` file, and can be references using the syntax `${{root.path.to.var}}`.

````{admonition} Environment variables vs. relative paths
:class: tip

Note that the only difference between and environment variable and relative path syntax is the inclusion of spaces in
the former (`${{ var }}`), and the omission of spaces in the latter (`${{path}}`).

````
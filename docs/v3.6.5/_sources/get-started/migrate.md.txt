# Migrate Jina 2 to Jina 3

Jina 3 comes with many improvements but to be able to enjoy them, you will also have to make some
tweaks to your existing Jina 2 code.

One of the major changes in Jina 3 is [DocArray](https://docarray.jina.ai/) being an external dependency:
The previously included `Document` and `DocumentArray` data structures now form their own library and include new
features, improved performance, and increased flexibility.

Accordingly, most of the breaking changes that users will experience when updating to Jina 3 are mainly related to `Document` and `DocumentArray`.

```{admonition} DocArray library
:class: seealso
[DocArray](https://docarray.jina.ai/) is our new library that includes the `Document` and `DocumentArray` data
structures. Inside their own library, `Document` and `DocumentArray` are faster and more versatile than ever, and
underpin neural search apps as well as the Jina ecosystem, including [Jina](https://docs.jina.ai/) and
[Finetuner](https://finetuner.jina.ai/).
```

In general, the breaking changes are aiming for increased simplicity and consistency, making your life easier in the
long run. Here you can find out what exactly you will have to adapt.

## Simple changes at a glance

Many of the changes introduced in Jina 3 are easily adapted to a Jina 2 codebase.
The modifications in the following table should, in most cases, be safe to perform without further thought or effort.


| Jina 2                                                  | Jina 3                                                |
|---------------------------------------------------------|-------------------------------------------------------|
| `doc.blob`                                              | `doc.tensor`                                          |
| `doc.buffer`                                            | `doc.blob`                                            |
| `docs.get_attributes('attribute')`                      | `docs[:, 'attribute']`                                |
| `['path1', 'path2']`                                    | `'path1,path2'`                                       |
| `docs.traverse_flat(paths)`                             | `docs['@paths']`                                      |
| `docs.flatten()`                                        | `docs[...]`                                           |
| `doc.SerializeToString()`                               | `doc.to_bytes()`                                      |
| `Document(bytes)`                                       | `Document.from_bytes()`                               |
| `from jina import Document, DocumentArray`              | `from docarray import Document, DocumentArray`        |


There are, however, some more nuanced changes in Jina 3 as well.
These are outlined below.


## Document: More natural attribute names and Pythonic serialization

Docarray introduces more natural naming conventions for `Document` and `DocumentArray` attributes.

- `doc.blob` is renamed to `doc.tensor`, to align with external libraries like PyTorch and Tensorflow
- `doc.buffer` is renamed to `doc.blob`, to align with the industry standard
- `doc.SerializeToString()` is removed in favour of `doc.to_bytes()` and `doc.to_json()`
- Creating a `Document` from serialized data using `Document(bytes)` is removed in favour of
`Document.from_bytes(bytes)` and `Document.from_json(bytes)`

## DocumentArray: Simplified attribute, element access and new storage options

```{admonition} DocArray library
:class: seealso

Take a look at the [DocArray documentation](https://docarray.jina.ai/fundamentals/documentarray/access-attributes/) 
to have a better understanding of accessing attributes and elements with `DocArray` 
```

**Attributes**: Docarray introduces a flexible way of bulk-accessing attributes of `Document`s in a `DocumentArray`.
- Instead of having to call `docs.get_attributes('attribute')`, you can simply call `docs.attributes` for
  a select number of attributes. Currently, this syntax is supported by:
  - `text`: `docs.texts`
  - `blob`: `docs.blobs`
  - `tensor`: `docs.tensors`
  - `content`: `docs.contents`
  - `embedding`: `docs.embeddings`
- The remaining attributes can be accessed in bulk by calling `docs[:, 'attribute']`, e.g. `docs[:, 'tags']`.
  Additionally, you can access a specific key in `tags` by calling `docs[:, 'tags__key']`.

**Array traversal**: For traversing `DocumentArray`s via a `traversal_path`, docarray introduces a simplified notation

- Traversal paths of the form `[path1, path2]` (e.g. `['r', 'cm']`) are replaced by a single string of the form
`'path1,path2'` (e.g. `'r,cm'`)
- `docs.traverse_flat(path)` is replaced by `docs['@path']` (e.g. `docs['@r,cm']`)
- `docs.flatten()` is replaced by `docs[...]`

````{tab} Jina 2

```python
from jina import Document, DocumentArray

docs = nested_docs()

print(docs.traverse_flat('r,c').texts)
```
```
>>> ['root1', 'rooot2', 'chunk11', 'chunk12', 'chunk21', 'chunk22']
```
```python
print(docs.flatten().texts)
```
```
>>> ['chunk11', 'chunk12', 'root1', 'chunk21', 'chunk22', 'root2']

```

````

````{tab} Jina 3 

```python
from docarray import Document, DocumentArray

docs = nested_docs()

print(docs['@r,c'].texts)
```
```
>>> ['root1', 'rooot2', 'chunk11', 'chunk12', 'chunk21', 'chunk22']
```
```python
print(docs[...].texts)
```
```
>>> ['chunk11', 'chunk12', 'root1', 'chunk21', 'chunk22', 'root2']

```

````

**Loading data from files**: DocumentArray introduces a `.from_files()` class method which can be used directly instead of
importing a `from_files()` function.

````{tab} Jina 2

```python
from jina import Document, DocumentArray
from jina.types.document.generators import from_files

docs = DocumentArray(from_files('path/to/files'))
```

````

````{tab} Jina 3 

```python
from docarray import Document, DocumentArray

docs = DocumentArray.from_files('path/to/files')
```

````

\
**Batching**: Batching operations are delegated to the docarray package and Python builtins:

- `docs.batch()` does not accept the arguments `traversal_paths=` and `require_attr=` anymore.
The example below shows how to achieve complex behavior that previously relied on these arguments, in a more Pythonic
and Jina 3 compatible way:

````{tab} Jina 2

```python
docs.batch(traversal_paths=paths, batch_size=bs, require_attr='attr')
```

````

````{tab} Jina 3 

```python
DocumentArray(filter(lambda x: bool(x.attr), docs['@paths'])).batch(batch_size=bs)
```

````
\
**Accessing non-existent values**: In Jina 2, bulk-accessing attributes in a `DocumentArray` returns a list of empty values, when the `Document`s
inside the `DocumentArray` do not have a value for that attribute. In Jina 3, this returns `None`. This change becomes
important when migrating code that checks for the presence of a certain attribute.

````{tab} Jina 2

```python
from jina import Document, DocumentArray

d = Document()
print(d.text)
```
```
>>> ''
```
```python
docs = DocumentArray([d, d])
print(docs.texts)
```
```
>>> ['', '']
```

````

````{tab} Jina 3 

```python
from docarray import Document, DocumentArray

d = Document()
print(d.text)
```
```
>>> ''
```
```python
docs = DocumentArray([d, d])
print(docs.texts)
```
```
>>> None
```

````
\
**Serialization**: `DocumentArray` introduces the same Pythonic serialization syntax as `Document`.
  - `docs.SerializeToString()` is removed in favour of `docs.to_bytes()` and `docs.to_json()`
  - Creating a `DocumentArray` from serialized data using `DocumentArray(bytes)` is removed in favour of
  `DocumentArray.from_bytes(bytes)` and `DocumentArray.from_json(bytes)`


**New storage options**:

Jina 2 used to offer persistence of DocumentArray through `DocumentArrayMemmap`. In Jina 3, this data structure is 
deprecated and we introduce different [Document Stores](https://docarray.jina.ai/advanced/document-store/) within the 
`DocumentArray` API. Thus, you can enjoy a consistent `DocumentArray` API across different storage backends and leverage
 modern databases.

For example, you can use [SQLite backend](https://docarray.jina.ai/advanced/document-store/sqlite/) as a replacement 
for `DocumentArrayMemmap`, which lets you persist Documents to disk and load them in another session:

````{tab} Storing to disk
```python
from docarray import Document, DocumentArray

das = DocumentArray(
    storage='sqlite',
    config={'connection': 'my_connection', 'table_name': 'my_table_name'},
)
das.extend([Document() for _ in range(10)])
```
````

````{tab} Loading from disk
```python
from docarray import DocumentArray

das = DocumentArray(
    storage='sqlite',
    config={'connection': 'my_connection', 'table_name': 'my_table_name'},
)
print(len(das))
```

```text
10
```
````

The API is **almost the same** as the deprecated `DocumentArrayMemmap` and is consistent across storage backends and 
in-memory storage. Furthermore, some Document Stores offer fast Nearest Neighbor algorithms and are more convenient in 
production.


## Flow and Client: Simplified `.post()` behavior

`client.post()` and `flow.post()` now return a flattened `DocumentArray` instead of a list of `Response`s when no
callback function is specified.

`.post()` can still be configured to return a list of Responses, by passing `return_responses=True` to the Client or Flow
constructors.


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

## Common errors and solutions

`AttributeError: 'Document' object has no attribute 'buffer'`
<details>
  <summary>Solution</summary>

Replace `doc.buffer` with `doc.blob` in your entire codebase
</details>

`RuntimeError: Could not infer dtype of NoneType` while performing `doc.embed()`
<details>
  <summary>Solution</summary>

Replace `doc.blob` with `doc.tensor` in your entire codebase
</details>

`AttributeError: 'DocumentArray' object has no attribute 'get_attributes'`
<details>
  <summary>Solution</summary>

Replace `docs.get_attributes('attribute')` with `docs[:, 'attribute']`
</details>

`AttributeError: 'Document' object has no attribute 'SerializeToString'`

<details>
  <summary>Solution</summary>

Replace `doc.SerializeToString` with `doc.to_bytes` or `doc.to_json`
</details>

`ValueError: Failed to initialize docarray.document.Document from obj=b"..."`
<details>
  <summary>Solution</summary>

Replace `Document(bytes)` with `Document.from_bytes(bytes)`
</details>

`TypeError: batch() got an unexpected keyword argument 'traversal_paths'`
<details>
  <summary>Solution</summary>

Replace `docs.batch(traversal_path='path', batch_size=bs)` with `docs['@path'].batch(batch_size=bs)`
</details>

`TypeError: batch() got an unexpected keyword argument 'require_attr'`
<details>
  <summary>Solution</summary>

Replace `docs.batch(traversal_path='path', require_attr='attr')` with
`DocumentArray(filter(lambda x: bool(x.attr)), docs).batch(batch_size=bs)`
</details>

`AttributeError: 'Document' object has no attribute 'docs'` when operating on the output of `flow.post()`
<details>
  <summary>Solution</summary>

Remove `resp[i].docs` as `flow.post()` already returns a `DocumentArray`
</details>
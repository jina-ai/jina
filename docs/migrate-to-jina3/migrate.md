# Migration to Jina 3

Jina 3 introduces a number of exciting features, but to be able to enjoy them, you will also have to make some
tweaks to your existing Jina 2 code.

One of the major changes in Jina 3 is the inclusion of the [docarray library](https://docarray.jina.ai/).
Accordingly, the scope of the changes in Jina 3 will be mainly related to `Document` and `DocumentArray`.
Here you can find out what exactly you will have to change.

## Attribute renamings

Docarray introduces more natural naming conventions for `Document` and `DocumentArray` attributes.

- `doc.blob` is renamed to `doc.tensor`, to align with external libraries like PyTorch and Tensorflow
- `doc.buffer` is renamed to `doc.blob`, to align with the industry standard

## Accessing attributes and elements

Docarray introduces a flexible way of accessing attributes of `Document`s in a `DocuemntArray`, in bulk.
- Instead of having to call `docs.get_attributes('attribute')`, you can simply call `docs.attributes` for
  a select number of attibutes. Currently, this syntax is supported by:
  - `text`: `docs.texts`
  - `blob`: `docs.blobs`
  - `tensor`: `docs.tensors`
  - `content`: `docs.contents`
  - `embedding`: `docs.embeddings`
- The remaining attributes can be accessed in bulk by calling `docs[:, 'attribute']`, e.g. `docs[:, 'tags']`.
  Additionally, you can access a specific key in `tags` by calling `docs[:'tags__key']`.

For traversing `DocumentArray`s via a `traversal_path`, docarray introduces a simplified notation:

- Traversal paths of the form `[path1, path2]` (e.g. `['r', 'cm']`) are replaced by a single string of the form
`'path1,path2'` (e.g. `'r,cm'`)
- `docs.traverse_flat(path)` is replaced by `docs['@path']` (e.g. `docs['@r,cm']`)
- `docs.flatten()` is replaced by `docs[...]`

Batching operations are delegated to the docarray package and Python builtins:

- `docsarray.batch()` does not accept the arguments `traversal_paths=` and `require_attr=` anymore.
To achieve previously allowed behaviours like `docs.batch(traversal_paths=paths, batch_size=bs, require_attr='attr')`
use the simplified `.batch()` method in combination with Python's `filter()`:
`DocumentArray(filter(lambda x : bool(x.attr), docs[path])).batch(batch_size=bs)`

## Method behaviour changes

- `flow.post()` now returns a flattened `DocumentArray` instead of a list of `Response`s, if `return_results=True` is
set. This makes it easier to immediately use the returned results. The behaviour of `client.post()` remains unchanged
compared to Jina 2, exposing entire `Response`s to the user. By setting or unsetting the `results_as_docarray=` flag,
the user can override these default behaviours.
- In Jina 2, bulk accessing attributes in a `DocumentArray` returns a list of empty values, when the `Document`s
inside the `DocumentArray` do not have a value for that attribute. In Jina 3, this returns `None`. This change becomes
important when migrating code that checks for the presence of a certain attribute.


## Serialization

- `docs.SerializeToString()` is removed in favour of `doc.to_bytes()`
- Creating a `Document` from serialized data using `Document(bytes)` is removed in favour of
`Document.from_bytes(bytes)`


## YAML parsing

In Jina 3, yaml syntax is aligned with [github actions notation](https://docs.github.com/en/actions/learn-github-actions/environment-variables),
which leads to the following changes:

- Referencing environment variables using the syntax `${{ VAR }}` is no longer allowed. The posix notations for
environment variables, `$var`, has been deprecated. Instead, use `${{ ENV.VAR }}`.
- The syntax `${{ VAR }}` now defaults to signifying a context variable, passed in a `dict()`. If you want to be explicit
about the use of context variables, you can use `${{ CONTEXT.VAR }}`.
- Relative paths can point to other variables within the same `.yaml` file, and can be references using the syntax
- `${{root.path.to.var}}`. Note the omission of spaces in this syntax definition.
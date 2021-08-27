## DocumentArrayMemmap API

When your `DocumentArray` object contains a large number of `Document`, holding it in memory can be very demanding. You
may want to use `DocumentArrayMemmap` to alleviate this issue. A `DocumentArrayMemmap` stores all Documents directly on
the disk, while keeping a small lookup table in memory and a buffer pool of documents with a fixed size. The lookup 
table contains the offset and length of each `Document`, hence it is much smaller than the full `DocumentArray`.
Elements are loaded on-demand to memory during the access. Memory-loaded documents are kept in the buffer pool to allow 
modifying documents.

The next table show the speed and memory consumption when writing and reading 50,000 `Documents`.

|| `DocumentArrayMemmap` | `DocumentArray` |
|---|---|---|
|Write to disk | 0.62s | 0.71s |
|Read from disk | 0.11s | 0.20s |
|Memory usage | 20MB | 342MB |
|Disk storage | 14.3MB | 12.6MB |

### Create `DocumentArrayMemmap`

```python
from jina.types.arrays.memmap import DocumentArrayMemmap

dam = DocumentArrayMemmap('./my-memmap')
```

### Add Documents to `DocumentArrayMemmap`

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])
```

The `dam` object stores all future Documents into `./my-memmap`, there is no need to manually call `save`/`reload`.
Recently added, modified or accessed documents are also kept in the memory buffer so all changes to documents are 
applied first in the memory buffer and will be persisted to disk lazily (e.g when they quit the buffer pool or when
the `dam` object's destructor is called). If you want to instantly persist the changed documents, you can call `save`.


### Buffer pool
A fixed number of documents are kept in the memory buffer pool. The number can be configured with the constructor
parameter `buffer_pool_size` (1000 by default). Only the `buffer_pool_size` most recently accessed, modified or added
documents exist in the pool. Replacement of documents uses the LRU strategy.

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document
dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
dam.extend([Document() for _ in range(100)])
```

The buffer pool ensures that in-memory modified documents are persisted to disk. Therefore, you should not reference 
documents manually and modify them if they might be outside of the buffer pool. The next section explains the best 
practices when modifying documents.

### Modifying elements of `DocumentArrayMemmap`

Modifying elements of a `DocumentArrayMemmap` is possible due to the fact that accessed and modified documents are kept
in the buffer pool:

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])

dam[0].text = 'goodbye'

print(dam[0].text)
```

```text
goodbye
```

However, there are practices to **avoid**. Mainly, you should not modify documents that you reference manually and that 
might not be in the buffer pool. Here are some practices to avoid:

1. Keep more  references than the buffer pool size and modify them:

````{tab} ❌ Don't
```python
from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap

docs = [Document(text='hello') for _ in range(100)]
dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
dam.extend(docs)
for doc in docs:
    doc.text = 'goodbye'

dam[50].text
```
   
```text
hello
```
````

````{tab} ✅ Do
Use the dam object to modify instead:

```python
from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap

docs = [Document(text='hello') for _ in range(100)]
dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
dam.extend(docs)
for doc in dam:
    doc.text = 'goodbye'

dam[50].text
```

```text
goodbye
```

It's also okay if you reference docs less than the buffer pool size:

```python
from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap

docs = [Document(text='hello') for _ in range(100)]
dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=1000)
dam.extend(docs)
for doc in docs:
    doc.text = 'goodbye'

dam[50].text
```

```text
goodbye
```
````

2. Modify a reference that might have left the buffer pool :

````{tab} ❌ Don't
```python
from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap

dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
my_doc = Document(text='hello')
dam.append(my_doc)

# my_doc leaves the buffer pool after extend
dam.extend([Document(text='hello') for _ in range(99)])
my_doc.text = 'goodbye'
dam[0].text
```

```text
hello
```
````

````{tab} ✅ Do
Get the document from the dam object and then modify it:

```python
from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap

dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
my_doc = Document(text='hello')
dam.append(my_doc)

# my_doc leaves the buffer pool after extend
dam.extend([Document(text='hello') for _ in range(99)])
dam[my_doc.id].text = 'goodbye' # or dam[0].text = 'goodbye'
dam[0].text
```

```text
goodbye
```
````


To summarize, it's a best practice to **rely on the `dam` object to reference the docs that you modify**.

### Clear a `DocumentArrayMemmap`

To clear all contents in a `DocumentArrayMemmap` object, simply call `.clear()`. It will clean all content on disk.

#### Pruning

One may notice another method `.prune()` that shares similar semantics. `.prune()` method is designed for "
post-optimizing" the on-disk data structure of `DocumentArrayMemmap` object. It can reduce the on-disk usage.

### Side-by-side vs. `DocumentArray`

Accessing elements in `DocumentArrayMemmap` is _almost_ the same as `DocumentArray`, you can use integer/string index to
access element; you can loop over a `DocumentArrayMemmap` to get all `Document`; you can use `get_attributes`
or `traverse_flat` to achieve advanced traversal or getter.

This table summarizes the interfaces of `DocumentArrayMemmap` and `DocumentArray`:

|| `DocumentArrayMemmap` | `DocumentArray` |
|---|---|---|
| `__getitem__`, `__setitem__`, `__delitem__` (int) | ✅|✅|
| `__getitem__`, `__setitem__`, `__delitem__` (string) | ✅|✅|
| `__getitem__`, `__delitem__` (slice)  |✅ |✅|
| `__iter__` |✅|✅|
| `__contains__` |✅|✅|
| `__len__` | ✅|✅|
| `append` | ✅|✅|
| `extend` | ✅|✅|
| `traverse_flat`, `traverse` | ✅|✅|
| `get_attributes`, `get_attributes_with_docs` | ✅|✅|
| `insert` |❌ |✅|
| `reverse` (inplace) |❌ |✅|
| `sort` (inplace) | ❌|✅|
| `__add__`, `__iadd__` | ❌|✅|
| `__bool__` |✅|✅|
| `__eq__` |✅|✅|
| `sample` |✅ |✅|
| `shuffle` |✅ |✅|
| `split` |✅ |✅|
| `match` (L/Rvalue) |✅|✅|
| `visualize` |✅|✅|

### Convert between `DocumentArray` and `DocumentArrayMemmap`

```python
from jina import Document, DocumentArray
from jina.types.arrays.memmap import DocumentArrayMemmap

da = DocumentArray([Document(text='hello'), Document(text='world')])

# convert DocumentArray to DocumentArrayMemmap
dam = DocumentArrayMemmap('./my-memmap')
dam.extend(da)

# convert DocumentArrayMemmap to DocumentArray
da = DocumentArray(dam)
```

### Maintaining consistency via `.reload()` and `.save()`

Considering two `DocumentArrayMemmap` objects that share the same on-disk storage `./memmap` but sit in different
processes/threads. After some writing ops, the consistency of the lookup table and the buffer pool may be corrupted, as
each `DocumentArrayMemmap` object has its own version of lookup table and buffer pool in memory. `.reload()` and 
`.save()` are for solving this issue:

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam2 = DocumentArrayMemmap('./my-memmap')

dam.extend([d1, d2])
assert len(dam) == 2
assert len(dam2) == 0

dam2.reload()
assert len(dam2) == 2

dam.clear()
assert len(dam) == 0
assert len(dam2) == 2

dam2.reload()
assert len(dam2) == 0
```
You don't need to use `.save` if you add new documents. However, if you modified an attribute of a document, you need
to use it:

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')

dam = DocumentArrayMemmap('./my-memmap')
dam2 = DocumentArrayMemmap('./my-memmap')

dam.append(d1)
d1.text = 'goodbye'
assert len(dam) == 1
assert len(dam2) == 0

dam2.reload()
assert len(dam2) == 1
assert dam2[0].text == 'hello'

dam.save()
dam2.reload()
assert dam2[0].text == 'goodbye'
```

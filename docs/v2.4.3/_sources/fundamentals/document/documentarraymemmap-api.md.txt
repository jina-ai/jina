(documentarraymemmap-api)=
# DocumentArrayMemmap

`DocumentArrayMemmap` is a drop-in replacement of `DocumentArray` in memory-demanding cases. It shares {ref}`nearly all APIs<api-da-dam>` with `DocumentArray`. 

When your `DocumentArray` object contains a large number of `Document`, holding it in memory can be very demanding. You
may want to use `DocumentArrayMemmap` to alleviate this issue. 


A `DocumentArrayMemmap` stores all Documents directly on
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

## Basics

### Create

```python
from jina import DocumentArrayMemmap

dam = DocumentArrayMemmap()  # use a local temporary folder as storage
dam2 = DocumentArrayMemmap('./my-memmap')  # use './my-memmap' as storage
```

### Add elements

```{code-block} python
---
emphasize-lines: 7
---
from jina import DocumentArrayMemmap, Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])
```

The `dam` object stores all Documents into `./my-memmap` folder on the disk, there is no need to manually call save or load.

```{tip}
You can of course use `.append()` to add single Document. But when adding multiple Documents, `.extend()` is much more efficient.
```

### Clear elements

To clear all contents in a `DocumentArrayMemmap` object, simply call `.clear()`. It will clean all content on the disk.

You can also check the disk usage of a `DocumentArrayMemmap` by `.physical_size`. 

### Convert to/from DocumentArray

```python
from jina import Document, DocumentArray, DocumentArrayMemmap

da = DocumentArray([Document(text='hello'), Document(text='world')])

# convert DocumentArray to DocumentArrayMemmap
dam = DocumentArrayMemmap('./my-memmap')
dam.extend(da)

# convert DocumentArrayMemmap to DocumentArray
da = DocumentArray(dam)
```

## Advanced

DocumentArrayMemmap is in general used for one-way access, either read-only or write-only. Interleaving reading and writing on a DocumentArrayMemmap is not safe and not recommended in production.  

### Understand buffer pool

Recently added, modified or accessed documents are kept in an in-memory buffer pool. This allows all changes to Documents 
applied first in the memory and then be persisted to disk in a lazy way (i.e. when they quit the buffer pool or when
the `dam` object's destructor is called). If you want to instantly persist the changed documents, you can call `.flush()`.

The number can be configured with the constructor
argument `buffer_pool_size` (1000 by default). Only the `buffer_pool_size` most recently accessed, modified or added
documents exist in the pool. Replacement of documents follows the LRU strategy.

```python
from jina import DocumentArrayMemmap

dam = DocumentArrayMemmap('./my-memmap', buffer_pool_size=10)
```

````{admonition} Warning
:class: warning
The buffer pool ensures that in-memory modified documents are persisted to disk. Therefore, you should not reference 
documents manually and modify them if they might be outside of the buffer pool. The {ref}`next section <modify-memmap>` 
explains the best practices when modifying documents.
````




(modify-memmap)=
### Modify elements

Modifying elements of a `DocumentArrayMemmap` is possible due to the fact that accessed and modified documents are kept
in the buffer pool:

```python
from jina import DocumentArrayMemmap, Document

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
    ```{code-block} python
    ---
    emphasize-lines: 6, 7
    ---
    from jina import Document, DocumentArrayMemmap 
    
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
    
    ```{code-block} python
    ---
    emphasize-lines: 6, 7
    ---
    from jina import Document, DocumentArrayMemmap
    
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
    
    ```{code-block} python
    ---
    emphasize-lines: 3, 4
    ---
    from jina import Document, DocumentArrayMemmap
    
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
    ```{code-block} python
    ---
    emphasize-lines: 9
    ---
    from jina import Document, DocumentArrayMemmap
    
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
    
    ```{code-block} python
    ---
    emphasize-lines: 10
    ---
    from jina import Document, DocumentArrayMemmap
    
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

### Maintain consistency

Considering two `DocumentArrayMemmap` objects that share the same on-disk storage `./memmap` but sit in different
processes/threads. After some writing ops, the consistency of the lookup table and the buffer pool may be corrupted, as
each `DocumentArrayMemmap` object has its own version of lookup table and buffer pool in memory. `.reload()` and 
`.flush()` are for solving this issue:

```python
from jina import Document, DocumentArrayMemmap

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
You don't need to call `.flush()` if you add new documents. However, if you modified an attribute of a document, you need
to use it:

```python
from jina import Document, DocumentArrayMemmap

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

dam.flush()
dam2.reload()
assert dam2[0].text == 'goodbye'
```


(api-da-dam)=
## API side-by-side vs. DocumentArray

The API of `DocumentArrayMemmap` is _almost_ the same as `DocumentArray`, you can use integer/string index to
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
| `plot_embeddings` |✅|✅|
| `plot_image_sprites` |✅|✅|
| `batch` | ✅|✅|
| `flatten` | ✅|✅|
| `.save`, `.load`, `.save_binary`, `.load_binary`, `.save_json`, `.load_json`, `.save_csv`, `.load_csv` |✅|✅|

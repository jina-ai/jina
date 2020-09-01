# Input and Output Functions in Jina

This document explains the input and output functions of Jina's Flow API.

## Input Function

### TL;DR
- By default, everything is sent in a buffer
- Use a crafter to handle the input
- Shortcuts such as `index_lines`, `index_ndarray` and `index_files` are available to input predefined formats. 

In the [Flow API](../flow/index.md), we highlight that you can use `.index()`, `.search()` and `.train()` to feed index data and search queries to a Flow:

```python
with f:
    f.index(input_fn)
```

```python
with f:
    f.search(input_fn, top_k=50, output_fn=print)
```

`input_fn` is `Iterator[bytes]`, each of which corresponds to a bytes representation of a Document.

A simple `input_fn` can be defined as follows:for

```python
def input_fn():
    for _ in range(10):
        yield b'look! i am a Document!'  # `s` is a "Document"! 


# or ...
input_fn = (b'look! i am a Document!' for _ in range(10))
```

### Shortcuts

| Function                          | Description                                                          |
| ---                               | ---                                                                  |
| `index_files`, `search_files`     | Use a list of files as the index/query source for the current Flow   |
| `index_lines`, `search_lines`     | Use a list of lines as the index/query source for the current Flow   |
| `index_ndarray`, `search_ndarray` | Use a Numpy `ndarray` as the index/query source for the current Flow |

### Why Bytes/Buffer?

You may wonder why we use bytes instead of some Python native objects as the input. There are two reasons: 

- As a universal search framework, Jina accepts documents in different formats, from text to image to video. Raw bytes is the only consistent data representation over those modalities.
- Clients can be written in languages other than Python. Raw bytes is the only data type that can be recognized across languages.

### But Then How Can Jina Recognize Those Bytes?

The answer relies on the Flow's `crafter`, and the "type recognition" is implemented as a "deserialization" step. The `crafter` is often the Flow's first component, and translates the raw bytes into a Python native object. 

For example, let's say our input function reads gif videos in binary:
 
```python
def input_fn():
    for g in all_gif_files:
        with open(g, 'rb') as fp:
            yield fp.read()

```

The corresponding `crafter` takes whatever is stored in the `buffer` and tries to make sense out of it:

```python
import io
from PIL import Image
from jina.executors.crafters import BaseDocCrafter

class GifCrafter(BaseDocCrafter):
    def craft(self, buffer):
        im = Image.open(io.BytesIO(buffer))
        # manipulate the image here
        # ...
``` 

In this example, `PIL.Image.open` takes either the filename or file object as argument. We convert `buffer` to a file object here using `io.BytesIO`.

Alternatively, if your input function is only sending the file name, like:

```python
def input_fn():
    for g in all_gif_files:
        yield g.encode()  # convert str to binary string b'str'
```

Then the corresponding `crafter` should change accordingly.

```python

from PIL import Image
from jina.executors.crafters import BaseDocCrafter

class GifCrafter(BaseDocCrafter):
    def craft(self, buffer):
        im = Image.open(buffer.decode())
        # manipulate the image here
        # ...
``` 

`buffer` now stores the file path, so we convert it back to a normal string with `.decode()` and read from the file path.

You can also combine two types of data, like:

```python
def input_fn():
    for g in all_gif_files:
        with open(g, 'rb') as fp:
            yield g.encode() + b'JINA_DELIM' + fp.read()
```

The `crafter` then can be implemented as:

```python
from jina.executors.crafters import BaseDocCrafter
import io
from PIL import Image

class GifCrafter(BaseDocCrafter):

    def craft(self, buffer, *args, **kwargs):
        file_name, img_raw = buffer.split(b'JINA_DELIM')
        im = Image.open(io.BytesIO(img_raw))
        # manipulate the image and file_name here
        # ...

```

As you can see from the examples above, we can use `buffer` to transfer strings and gif videos.

`.index()`, `.search()` and `.train()` also accept `batch_size` which controls the number of Documents per request. However, this does not change the `crafter`'s implementation, as the `crafter` always works at the Document level. 

Further reading:
- [`jina client --help`](../cli/jina-client.html)
- [Jina `Document` Protobuf](../proto/docs.html#document)
- [`prefetch` in `jina gateway`](../cli/jina-gateway.html?highlight=prefetch#gateway%20arguments)


## Output Function

### TL;DR

- Everything works asynchronously
- Use `callback=` to specify the output function

Jina's output function is basically *asynchronous callback*. [For](For) the sake of efficiency, Jina is designed to be highly asynchronous on data transmission. You just keep sending requests to Jina without any blocking. When a request is finished, the callback function is invoked.

For example, the following will print the request after a `IndexRequest` is finished:

```python
with f:
    f.index(input_fn, output_fn=print)
```  

This is quite useful when debugging.

In the "Hello, World!" example, we use a callback function to append the top-k results to an HTML page:

```python
def print_html(resp):
    for d in resp.search.docs:
        vi = 'data:image/png;base64,' + d.meta_info.decode()
        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        for kk in d.matches:
            kmi = 'data:image/png;base64,' + kk.match_doc.meta_info.decode()
            result_html.append(f'<img src="{kmi}" style="opacity:{kk.score.value}"/>')
            # k['score']['explained'] = json.loads(kk.score.explained)
        result_html.append('</td></tr>\n')
```

```python
f.search(input_fn,
                 output_fn=print_html, top_k=args.top_k, batch_size=args.query_batch_size)
```

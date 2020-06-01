# Input and Output Functions in Jina

In this chapter I will explain the input and output design of Jina.


## Input Function

### TLDR;
- Everything is sent in bytes
- Use crafter to work with `buffer`

In the [Flow API](../flow/README.md), we highlight that you can use `.index()`, `.search()` and `.train()` to feed index data and search query to a flow:

```python
with f:
    f.index(input_fn)
```

```python
with f:
    f.search(input_fn, top_k=50, output_fn=print)
```

`input_fn` is `Iterator[bytes]`, each of which corresponds to a bytes representation of a Document.

A simple `input_fn` can be defined as follows:

```python
def input_fn():
    for _ in range(10):
        yield b'look! i am a Document!'  # `s` is a "Document"! 


# or ...
input_fn = (b'look! i am a Document!' for _ in range(10))
```

### Why in bytes?

Some users may wonder why we use bytes instead of some Python native objects as the input. There are two reasons behind: 

- As a universal search framework, Jina accepts documents in different formats, from text document, image to video. The only data representation that is consistent over those modalities is raw bytes.
- Client can be written in different languages other than Python. The only data type that can be recognized across the languages is raw bytes.

### But then how can you recognize those bytes in Jina?

The answer relies in the `crafter` in the Flow, and the "type recognition" is implemented as a "deserialization" step. The `crafter` is often the first component in the Flow, it translates the raw bytes into some Python native object. 

For example, let's say our input function is
 
```python
def input_fn():
    for g in all_gif_files:
        with open(g, 'rb') as fp:
            yield fp.read()

```

which basically reads gif video in binary.

The corresponding `crafter` takes whatever stored in `buffer` and try to make sense out of it:

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

Alternatively, if your input function is sending the file name only, e.g.

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

`buffer` now stores the file path, so we convert it back to normal string with `.decode()` and reads from the file path.

One can also combine two types of data together, e.g.

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

As you can see from the examples above, we use `buffer` to transfer string and gif video.

`.index()`, `.search()` and `.train()` also accept `batch_size` which controls the number of documents per each request. But this does not change the implementation of the `crafter`, as the `crafter` always works at document level. 

Further readings:
- [`jina client --help`](../cli/jina-client.html)
- [Jina `Document` Protobuf](../proto/docs.html#document)
- [`prefetch` in `jina gateway`](../cli/jina-gateway.html?highlight=prefetch#gateway%20arguments)


## Output Function

### TLDR;

- Everything works asynchronously
- Use `callback=` to specify the output function

The output function in Jina is basically *asynchronous callback*. For the sake of efficiency Jina is designed to be highly asynchronous on data transmission. You just keep sending request to Jina without any blocking. When a request is finished, the callback function will be invoked.

For example, the following will print the request after a `IndexRequest` is finished:

```python
with f:
    f.index(input_fn, output_fn=print)
```  

This is quite useful when debugging.

In the "Hello, World!" example, we use callback function to append the top-k result to a HTML page:

```python
def print_html(resp):
    for d in resp.search.docs:
        vi = 'data:image/png;base64,' + d.meta_info.decode()
        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        for kk in d.topk_results:
            kmi = 'data:image/png;base64,' + kk.match_doc.meta_info.decode()
            result_html.append(f'<img src="{kmi}" style="opacity:{kk.score.value}"/>')
            # k['score']['explained'] = json.loads(kk.score.explained)
        result_html.append('</td></tr>\n')
```

```python
f.search(input_fn,
                 output_fn=print_html, top_k=args.top_k, batch_size=args.query_batch_size)
```

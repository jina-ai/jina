# Input and Output Functions in Jina

This chapter explains the input and output functions of Jina's Flow API.

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

A simple `input_fn` can be defined as follows:

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


#### Usage of `index_ndarray()` 

```python
import numpy as np
from jina.flow import Flow

input_data = np.random.random((3,8))

f = Flow().add(uses='_logforward')

with f:
    f.index_ndarray(input_data)
```
    
* Add a dummy Pod with config `_logforward` to the Flow. [`_logforward`](https://docs.jina.ai/chapters/simple_exec.html) is a built-in YAML, which just forwards input data to the results and prints it to the log. It is located in `jina/resources/executors._forward.yml`. You can also use your own [YAML](https://docs.jina.ai/chapters/yaml/yaml.html) to organize `pods`.
* Use the Flow to index an `ndarray` by calling the `index_ndarray()` API. 

Calling the `index_ndarray()` API generates requests with the following message:

```
request {
  request_id: 1
  index {
    docs {
      id: 1
      weight: 1.0
      length: 100
      blob {
        buffer: "\004@\316\362/D\333?\244>\235\305\027\311\336?\267\210\251\311^\260\345?\366\n(\014\022m\356?\374\262\017\030\036\357\351?-c\300\337\217V\345?\241G\241\352\233\024\356?\340\346lUf\353\350?"
        shape: 8
        dtype: "float64"
      }
    }
    docs {
      id: 2
      weight: 1.0
      length: 100
      blob {
        buffer: "\312Wm\337\250\217\354?t\212\326\020\261\r\320?\254\262\300u<O\323?\340\210\222$\321\216\314?\310.q,+\347\311?&\316\361\310\252R\331?\214\016\201a\231\262\330?\342\231\262\221\343%\324?"
        shape: 8
        dtype: "float64"
      }
    }
    docs {
      id: 3
      weight: 1.0
      length: 100
      blob {
        buffer: "kT\250\372K%\345?\237\017+u\300\227\353?\3668\256\340\251\227\350?\327\006$\032$\002\341?\274\300\3573\371\262\343?\346\371\265dV\330\342?\370\210\360\002P3\340?\022i-\016\374\320\331?"
        shape: 8
        dtype: "float64"
      }
    }
  }
}
```

The structure of this message is defined in the format of [protobuf](https://docs.jina.ai/chapters/proto/docs.html). Check more details of the data structure at [`jina.proto`](https://docs.jina.ai/chapters/proto/docs.html#jina.proto). Messages are passed between the Pods in the Flow.

`request` contains input data and related metadata. The input is a 3*8 matrix that is sent to the Flow, which matches 3 `request.index.docs`, and the `request.index.docs.blog.shape` is 8. The vector of the matrix is stored in `request.index.docs.blob`, and the `request.index.docs.blob.dtype` indicates the type of the vector.

`search_ndarray()` is the API for searching `np.ndarray`. The data structure will be replaced from `request.index` to `request.search`, and the other nodes stay the same.

```python
import numpy as np
from jina.flow import Flow

input_data = np.random.random((3,8))

f = Flow().add(uses='_logforward')

with f:
    f.search_ndarray(input_data)
```

#### Usage of `index_files()`

```python
from jina.flow import Flow

f = Flow().add(uses='_logforward')

with f:
    f.index_files(f'../pokedex-with-bit/pods/*.yml')
```

API `index_files()` reads input data from `../pokedex-with-bit/pods/*.yml`. In this directory, there are 5 YAML files. Therefore, you can see them in the protobuf request as well:

* 5 `docs` under `request.index`
* Each file's path in a `request.index.doc.uri`

```protobuf
request {
  request_id: 1
  index {
    docs {
      id: 1
      weight: 1.0
      length: 100
      uri: "../pokedex-with-bit/pods/encode-baseline.yml"
    }
    docs {
      id: 2
      weight: 1.0
      length: 100
      uri: "../pokedex-with-bit/pods/chunk.yml"
    }
    docs {
      id: 3
      weight: 1.0
      length: 100
      uri: "../pokedex-with-bit/pods/doc.yml"
    }
    docs {
      id: 4
      weight: 1.0
      length: 100
      uri: "../pokedex-with-bit/pods/encode.yml"
    }
    docs {
      id: 5
      weight: 1.0
      length: 100
      uri: "../pokedex-with-bit/pods/craft.yml"
    }
  }
}

```

`search_files()` is the API for searching `files`. 

```python
from jina.flow import Flow

f = Flow().add(uses='_logforward')

with f:
    f.search_files(f'../pokedex-with-bit/pods/chunk.yml')
```

### Usage of `index_lines()`

```python
from jina.flow import Flow
input_str = ['aaa','bbb']

f = Flow().add(uses='_logforward')
with f:
    f.index_lines(lines=input_str)
``` 

`index_lines()` reads input data from `input_str`. As you can see above, there are 2 elements in `input_str`, so in the protobuf you can see:

* 2 `docs` under `request.index.docs`
* Each individual string in `request.index.docs.text`. 

```
request {
  request_id: 1
  index {
    docs {
      id: 1
      weight: 1.0
      length: 100
      mime_type: "text/plain"
      text: "aaa"
    }
    docs {
      id: 2
      weight: 1.0
      length: 100
      mime_type: "text/plain"
      text: "bbb"
    }
  }
}
```

`search_lines()` is the API for searching `text`. 

```python
from jina.flow import Flow

text = input('please type a sentence: ')

f = Flow().add(uses='_logforward')

with f:   
    f.search_lines(lines=[text, ])
```

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
from jina.executors.crafters import BaseCrafter

class GifCrafter(BaseCrafter):
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
from jina.executors.crafters import BaseCrafter

class GifCrafter(BaseCrafter):
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
from jina.executors.crafters import BaseCrafter
import io
from PIL import Image

class GifCrafter(BaseCrafter):

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

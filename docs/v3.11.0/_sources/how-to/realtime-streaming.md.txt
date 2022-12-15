# Build real-time streaming service

In this example, we'll build a real-time video streaming service like Zoom, allowing multiple users to chat via webcam. The whole solution is just twenty lines of code, showcasing Jina's power and ease of use.

![](https://user-images.githubusercontent.com/2041322/185625220-40c1f887-3be4-49df-9318-c49e0fb7365e.gif)

The source code [can be found here](https://github.com/jina-ai/jina-video-chat).

## Basic idea

The idea is straightforward: 

- Use a client-server architecture
- Client uses webcam and collects frames and sends them to the server
- Server aggregates all frames from different users and sends back to the client
- Client displays the received frames

## Client

The more technical and interesting part is on the client side. The key is to set `request_size=1` and use callback to handle response (instead of return).

```{tip}
You will need `opencv-python`, which you can install with `pip install opencv-python`.
```


```python
import sys
import cv2

if len(sys.argv) == 3:
    server_address = sys.argv[1]
    user = sys.argv[2]
else:
    print('Usage: ./client.py <server_address> <user>')
    sys.exit(1)


def render_recv(resp):
    for d in resp.docs:
        cv2.imshow('output', d.tensor)


from jina import Client, Document

c = Client(host=server_address)
c.post(
    '/',
    Document.generator_from_webcam(
        tags={'user': user}, show_window=False, height_width=(200, 300)
    ),
    on_done=render_recv,
    request_size=1,
)
```

We use [DocArray API `generator_from_webcam`](https://docarray.jina.ai/datatypes/video/#create-document-from-webcam) to create a Document generator from the webcam, where each frame is a `Document` with a `tensor` field.

Therefore, the input has infinite length, until you hit the `ESC` key.

To achieve real-time streaming, set `request_size` to 1. This means that the client doesn't do any batching and directly sends each Document as a request. You also need to use {ref}`callback-functions` to handle the response. This is different from using the return in many other examples. A callback ensures the user sees the response as soon as it is received.


## Server

The Server is super simple: Concatenate all frames from different users and send back to the client.

```python
import numpy as np
from jina import Executor, requests


class VideoChatExecutor(Executor):
    last_user_frames = {}

    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            self.last_user_frames[d.tags['user']] = d.tensor
            if len(self.last_user_frames) > 1:
                d.tensor = np.concatenate(list(self.last_user_frames.values()), axis=0)
```

Save it as `executor.py` and create `config.yml` with the following content:

```yaml
jtype: VideoChatExecutor
py_modules:
  - executor.py
```

Put both under the `executor/` folder and now the Flow YAML looks as follows:

```yaml
jtype: Flow
executors:
  - uses: executor/config.yml
    name: frameAggregator
```

The whole file structure is illustrated below:

```
flow.yml
executor/
    config.yml
    executor.py
```

## Run

First run the server:

```bash
jina flow --uses flow.yml
```

Note down the server address:

![](https://github.com/jina-ai/jina-video-chat/raw/main/.github/server.png)

Now run the client from different machines (in this case, `alice`, `bob` and `carol`):

```bash
python client.py grpcs://your-server-address-from-last-image alice
python client.py grpcs://your-server-address-from-last-image bob
python client.py grpcs://your-server-address-from-last-image carol
```

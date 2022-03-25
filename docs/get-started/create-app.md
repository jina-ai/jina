# Create a New Project

Let’s write a small application with our new Jina development environment. To start, we'll use Jina CLI to make a new project for us. In your terminal of choice run:

```bash
jina new hello-jina
```

This will generate a new directory called `hello-jina` with the following files:

```text
hello-jina
|- app.py
|- executor1/
        |- config.yml
        |- executor.py
```

- `app.py` is the entrypoint of your Jina project. You can run it via `python app.py`. 
- `executor1/` is where we'll write our Executor code.
- `config.yml` is the config file for the Executor. It’s where you keep metadata for your Executor, as well as dependencies.

There may be some other files like `README.md`, `manifest.yml`  `requirements.txt` to provide extra metadata about that Executor. More information {ref}`can be found here<create-executor>`.

```bash
cd hello-jina
python app.py
```

You should see this in your terminal:

```bash
           Flow@99300[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:52971
	🔒 Private network:	192.168.0.102:52971
	🌐 Public address:	84.172.88.250:52971
['hello, world!', 'goodbye, world!']
```

## Adding dependencies

You can use any third-party Python library in Executor. Let's create `executor1/requirements.txt` and `pytorch` to it.

Then in `executor.py`, let's add another endpoint `/get-tensor` as follows:

```python
import numpy as np
import torch

from jina import Executor, DocumentArray, requests


class MyExecutor(Executor):
    @requests(on='/get-tensor')
    def bar(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tensor = torch.tensor(np.random.random([10, 2]))
```

## A small Jina application


Now let's write a small application with our new dependency. In our `app.py`, add the following code:

```python
from jina import Flow, Document

f = Flow().add(uses='executor1/config.yml')

with f:
    da = f.post('/get-tensor', [Document(), Document()])
    print(da.tensors)
```

Once we save that, we can run our application by typing:

```bash
python app.py
```

Assuming everything went well, you should see your application print this to the screen:

```bash
       Flow@301[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:59667
	🔒 Private network:	192.168.0.102:59667
	🌐 Public address:	84.172.88.250:59667
tensor([[[0.9594, 0.9373],
         [0.4729, 0.2012],
         [0.7907, 0.3546],
         [0.6961, 0.7463],
         [0.3487, 0.7837],
         [0.7825, 0.0556],
         [0.3296, 0.2153],
         [0.2207, 0.0220],
         [0.9547, 0.9519],
         [0.6703, 0.4601]],

        [[0.9684, 0.6781],
         [0.7906, 0.8454],
         [0.2136, 0.9147],
         [0.3999, 0.7443],
         [0.2564, 0.0629],
         [0.4713, 0.1018],
         [0.3626, 0.0963],
         [0.7562, 0.2183],
         [0.9239, 0.3294],
         [0.2457, 0.9189]]], dtype=torch.float64
```
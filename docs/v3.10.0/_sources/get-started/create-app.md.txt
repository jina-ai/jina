# {octicon}`milestone` Create First Project

Let's build a toy application with Jina. To start, we use Jina CLI to make a new project for us:

```bash
jina new hello-jina
```

This will create a new project folder called `hello-jina` with the following file structure:

```text
hello-jina/
    |- client.py
    |- flow.yml
    |- executor1/
            |- config.yml
            |- executor.py
```

- `flow.yml` is the configuration file for the Jina Flow.
- `executor1/` is where we'll write our {class}`~jina.Executor` code.
- `config.yml` is the config file for the {class}`~jina.Executor`. It’s where you keep metadata for your Executor, as well as dependencies.
- `client.py` is the entrypoint of your Jina project. You can run it via `python app.py`.

There may be some other files like `README.md`, `requirements.txt` to provide extra metadata about that {class}`~jina.Executor`. More information {ref}`can be found here<create-executor>`.


Now run it and observe the output of the server and client.


````{tab} Run server
```shell
jina flow --uses flow.yml
```

```shell

──── 🎉 Flow is ready to serve! ────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:54321  │
│  🔒     Private    192.168.200.56:54321  │
│  🌍      Public    81.223.121.124:54321  │
╰──────────────────────────────────────────╯
```
````

````{tab} Run client
```bash
python client.py
```

```shell
['hello, world!', 'goodbye, world!']
```
````


## Add logics

You can use any Python library in {class}`~jina.Executor`. For example, let's add `pytorch` to `executor1/requirements.txt` and crunch some numbers. 

In `executor.py`, let's add another endpoint `/get-tensor` as follows:

```{code-block} python
---
emphasize-lines: 13-16
---
import numpy as np
import torch

from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'hello, world!'
        docs[1].text = 'goodbye, world!'

    @requests(on='/crunch-numbers')
    def bar(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tensor = torch.tensor(np.random.random([10, 2]))
```

Kill the last server by `ctrl-C` and restart the server by `jina flow --uses flow.yml`.

## Call `/crunch-number` endpoint

Modify `client.py` to call `/crunch-numbers` endpoint:

```python
from jina import Client, DocumentArray

if __name__ == '__main__':
    c = Client(host='grpcs://1655d050ad.wolf.jina.ai')
    da = c.post('/crunch-numbers', DocumentArray.empty(2))
    print(da.tensors)
```

Once we save that, we can run our new client:

```bash
python client.py
```

```text
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
         [0.2457, 0.9189]]], dtype=torch.float64)
```

## Deploy to JCloud

JCloud offers free CPU and GPU instances to host Jina project. Let's deploy our first project to JCloud.

```bash
jina auth login
```

Log in with your Github, Google or Email account.

```bash
jina cloud deploy ./
```

```{figure} deploy-jcloud-ongoing.png
```

Deployment is fully automatic and takes a few minutes.

After it is done, you should see the following message in the terminal.


```text
╭────────────── 🎉 Flow is available! ──────────────╮
│                                                   │
│   ID            1655d050ad                        │
│   Endpoint(s)   grpcs://1655d050ad.wolf.jina.ai   │
│                                                   │
╰───────────────────────────────────────────────────╯
```


Now let's change the Client's code to use the deployed endpoint shown above:

```{code-block} python
---
emphasize-lines: 4
---
from jina import Client, DocumentArray

if __name__ == '__main__':
    c = Client(host='grpcs://1655d050ad.wolf.jina.ai')
    da = c.post('/crunch-numbers', DocumentArray.empty(2))
    print(da.tensors)
```

```{tip}
The very first request can be a bit slow because the server is starting up.
```

```text
tensor([[[0.4254, 0.4305],
         [0.6200, 0.5783],
         [0.7989, 0.8742],
         [0.1324, 0.7228],
         [0.1274, 0.6538],
         [0.1533, 0.7543],
         [0.3025, 0.7702],
         [0.6938, 0.9289],
         [0.5222, 0.7280],
         [0.7298, 0.4923]],

        [[0.9747, 0.5026],
         [0.6438, 0.4007],
         [0.0899, 0.8635],
         [0.3142, 0.4142],
         [0.4447, 0.2540],
         [0.1109, 0.6260],
         [0.3850, 0.9894],
         [0.0845, 0.7538],
         [0.1444, 0.5136],
         [0.3368, 0.6162]]], dtype=torch.float64)
```

## Delete the deployed project

Don't forget to delete a Flow if you are not using it anymore.

```bash
jina cloud remove 1655d050ad
```


```text
Successfully removed Flow 1655d050ad.
```

You just finished your first Jina toy project, congrats! You can now start your own project.
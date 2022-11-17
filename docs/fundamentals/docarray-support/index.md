(docaray-dependency)=
# From DocArray to Jina

DocArray is an upstream dependency of Jina. Without DocArray, Jina can not run.

DocArray focuses on the local & monolith developer experience. [Jina](https://github.com/jina-ai/jina) scales DocArray to the Cloud. DocArray is also the default transit format in Jina, Executors talk to each other via serialized DocArray. The picture below shows their relations.

```{figure} position-jina-docarray.svg
:width: 80%

```

The next picture summarizes your development journey with DocArray and Jina. With a new project, first move horizontally left with DocArray, that often means improving quality and completing logics on a local environment. When you are ready, move vertically up with Jina, equipping your application with service endpoint, scalability and cloud-native features. Finally, you reach the point your service is ready for production.

```{figure} position-jina-docarray-2.svg
:width: 80%

```

## Direct invoke Jina/Hub Executor

As described {ref}`here <da-post>`, one can simply use an external Jina Flow/Executor as a regular function to process a DocumentArray. 

## Local code as a service

Considering the example below, where we use DocArray to pre-process an image DocumentArray:

```python
from docarray import Document, DocumentArray

da = DocumentArray.from_files('**/*.png')


def preproc(d: Document):
    return (
        d.load_uri_to_image_tensor()  # load
        .set_image_tensor_normalization()  # normalize color
        .set_image_tensor_channel_axis(-1, 0)
    )  # switch color axis for the PyTorch model later


da.apply(preproc).plot_image_sprites(channel_axis=0)
```

The code can be run as-is. It will give you a plot like the following (depending on how many images you have):

```{figure} docarray-img.png
:width: 50%
```


When writing it with Jina, the code is slightly refactored into the Executor-style:

```python
from docarray import Document, DocumentArray

from jina import Executor, requests


class MyExecutor(Executor):
    @staticmethod
    def preproc(d: Document):
        return (
            d.load_uri_to_image_tensor()  # load
            .set_image_tensor_normalization()  # normalize color
            .set_image_tensor_channel_axis(-1, 0)
        )  # switch color axis for the PyTorch model later

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.apply(self.preproc)
```

To summarize, you need to do three changes:

- Import `Executor` and subclass it;
- Wrap you functions into class methods;
- Add `@request` decorator the logic functions.

Now you can feed data to it via:

```python
from jina import Flow, DocumentArray

f = Flow().add(uses=MyExecutor)

with f:
    r = f.post('/', DocumentArray.from_files('**/*.png'), show_progress=True)
    r.plot_image_sprites(channel_axis=0)
```

You get the same results as before with some extra output from the console:

```text
           Flow@26202[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:57050
	🔒 Private network:	192.168.0.102:57050
	🌐 Public address:	84.172.88.250:57050
⠋       DONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸ 0:00:05 100% ETA: 0 seconds 80 steps done in 5 seconds
```

## Three good reasons to use Jina

Okay, so this code has been refactored from 10 lines to 24 lines, what's the deal? Here are three reasons to use Jina:

### A client-server architecture

One immediate consequence is now your logic works as a service. You can host it remotely on a server and start client to query it:

````{tab} Server
```python
from jina import Flow, DocumentArray

f = Flow(port=12345).add(uses=MyExecutor)

with f:
    f.block()
```
````
````{tab} Client
```python
from jina import Client, DocumentArray

c = Client(port=12345)
c.post('/', DocumentArray.from_files('**/*.png'), show_progressbar=True)
```
````

You can also use `websockets`, `http`, GraphQL API to query it. More details can be found in [Jina Documentation](https://docs.jina.ai/).

### Scale it out

Scaling your server is as easy as adding `replicas`:

```python
from jina import Flow

f = Flow(port=12345).add(uses=MyExecutor, replicas=3)

with f:
    f.block()
```

This will start three parallels can improve the overall throughput. [More details can be found here.](https://docs.jina.ai/fundamentals/flow/create-flow/#replicate-executors)

### Share and reuse it

One can share and reuse it via [Hub](https://hub.jina.ai). Save your Executor in a folder say `foo` and then:

```bash
jina hub push foo
```

This will upload your Executor logic to Jina Hub and allows you and other people to reuse it via Sandbox (as a hosted-microservice), Docker image or source. For example, after `jina hub push`, you will get:


```{figure} jinahub-push.png
:width: 60%
```


Say if you want to use it as a Sandbox, you can change your Flow to:

```python
from jina import Flow, DocumentArray

f = Flow().add(uses='jinahub+sandbox://mp0pe477')

with f:
    f.post('/', DocumentArray.from_files('**/*.png'), show_progressbar=True)
```

In this case, the Executor is running remotely and managed by Jina Cloud. It does not use any of your local resources.

A single Executor can do very limited things. You can combine multiple Executors together in a Flow to accomplish a task, some of them are written by you; some of them are shared from the Hub; some may run remotely; some may run in local Docker. Little you have to worry about, all you need is to keep doing `.add()` Executor to your Flow.

## Summary


If you start something new, start with DocArray. If you want to scale it out and make it a public available cloud-service, then use Jina.
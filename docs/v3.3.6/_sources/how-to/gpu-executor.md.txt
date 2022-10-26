(gpu-executor)=
# How to run Executors on GPU

This document will show you how to use an Executor on a GPU, both locally and in a
Docker container. You will also learn how to use GPU with pre-built Hub executors.

Using a GPU allows you to significantly speed up encoding for most deep learning models,
reducing response latency by anything from 5 to 100 times, depending on the model and inputs used.

```{admonition} Important
:class: important

This tutorial assumes you are already familiar with basic Jina concepts, such as Document, Executor, and Flow. Some knowledge of the [Hub](../fundamentals/executor/hub/index) is also needed for the last part of the tutorial.

If you're not yet familiar with these concepts, first read the [Executor](../fundamentals/executor/index) and [Flow](../fundamentals/executor/index) documentation, and return to this tutorial once you feel comfortable performing basic operations in Jina.
```

## Jina & GPUs in a nutshell

If you want a thorough walk-through of how to use GPU resources in your code, the full tutorial in the
[next section](#Prerequisites) is exactly what you are looking for.

But if you already know how to use your GPU and have come here just to find out how to make it play nice with Jina,
then we have good news for you:

You just use your GPU like you usually would in your machine learning framework of choice, and you are off to the races.
Jina enables you to use GPUs like you normally would in a Python script, or in a Docker 
container - it does not impose any additional requirements or configuration.


Let's take a look at a minimal working example, written in PyTorch.

```python
import torch

from docarray import DocumentArray
from jina import Executor, requests


class MyGPUExec(Executor):
    def __init__(self, device: str = 'cpu', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        with torch.inference_mode():
            # Generate random embeddings
            embeddings = torch.rand((len(docs), 5), device=self.device)
            docs.embeddings = embeddings
            embedding_device = 'GPU' if embeddings.is_cuda else 'CPU'
            docs.texts = [f'Embeddings calculated on {embedding_device}']
```


````{tab} Use it with CPU 

```python
from docarray import Document
from jina import Flow

f = Flow().add(uses=MyGPUExec, uses_with={'device': 'cpu'})
docs = DocumentArray(Document())
with f:
    docs = f.post(on='/encode', inputs=docs)
print(f'Document embedding: {docs.embeddings}')
print(docs.texts)
```

```console
           Flow@80[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:49618
	🔒 Private network:	172.28.0.2:49618
	🌐 Public address:	34.67.105.220:49618
Document embedding: tensor([[0.1769, 0.1557, 0.9266, 0.8655, 0.6291]])
['Embeddings calculated on CPU']

```

````

````{tab} Use it with GPU

```python
from docarray import Document
from jina import Flow

f = Flow().add(uses=MyGPUExec, uses_with={'device': 'cuda'})
docs = DocumentArray(Document())
with f:
    docs = f.post(on='/encode', inputs=docs)
print(f'Document embedding: {docs.embeddings}')
print(docs.texts)
```

```console
           Flow@80[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:56276
	🔒 Private network:	172.28.0.2:56276
	🌐 Public address:	34.67.105.220:56276
Document embedding: tensor([[0.6888, 0.8646, 0.0422, 0.8501, 0.4016]])
['Embeddings calculated on GPU']

```

````

Just like that, your code runs on GPU, inside a Jina `Flow`.

Next, we will go through a more fleshed out example in detail, where we use a language model to embed text in our
documents - all on GPU, and thus blazingly fast.

## Prerequisites

For this tutorial, you will need to work on a machine with an NVIDIA graphics card. You
can use various free cloud platforms (like Google Colab or Kaggle kernels), if you do
not have such a machine at home.

You will also need to make sure to have a recent version of [NVIDIA drivers](https://www.nvidia.com/Download/index.aspx)
installed. You don't need to install CUDA for this tutorial, but note that depending on
the deep learning framework that you use, that might be required (for local execution).

For the Docker part of the tutorial you will also need to have [Docker](https://docs.docker.com/get-docker/) and 
[nvidia-docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.

To run Python scripts you will need a virtual environment (for example [venv](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) or [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-environments)), and to install Jina inside it using

```bash
pip install jina
```

## Setting up the Executor


```{admonition} Jina Hub
:class: info

In this section we create an executor using [Jina Hub](https://hub.jina.ai/). This still creates your executor locally
and privately, but makes it quick and easy to run your
executor inside a Docker container, or to publish it to the Hub later, should you so choose.
```

We will create a simple sentence encoder, and we'll start by creating the Executor 
"skeleton" using Jina's command line utility:

```bash
jina hub new
```

When prompted for inputs, name your encoder `SentenceEncoder`, and accept the default
folder for it - this will create a `SentenceEncoder/` folder inside your current
directory, this will be our working directory for this tutorial. 

Next, select `y` when prompted for advanced configuration, and leave all other questions
empty, except when you are asked if you want to create a `Dockerfile` - answer `y` to 
this one (we will need it in the next section). In the end, you should be greeted with suggested next steps.

<details>
  <summary> Next steps </summary>

```bash
╭────────────────────────────────────── 🎉 Next steps ───────────────────────────────────────╮
│                                                                                            │
│  Congrats! You have successfully created an Executor! Here are the next steps:             │
│  ╭──────────────────────── 1. Check out the generated Executor ─────────────────────────╮  │
│  │   1 cd /home/ubuntu/SentenceEncoder                                                  │  │
│  │   2 ls                                                                               │  │
│  ╰──────────────────────────────────────────────────────────────────────────────────────╯  │
│  ╭─────────────────────────── 2. Understand folder structure ───────────────────────────╮  │
│  │                                                                                      │  │
│  │   Filena…   Description                                                              │  │
│  │  ──────────────────────────────────────────────────────────────────────────────────  │  │
│  │   config…   The YAML config file of the Executor. You can define __init__ argumen…   │  │
│  │             ╭────────────────── config.yml ──────────────────╮                       │  │
│  │             │   1                                            │                       │  │
│  │             │   2 jtype: SentenceEncoder                     │                       │  │
│  │             │   3 with:                                      │                       │  │
│  │             │   4     foo: 1                                 │                       │  │
│  │             │   5     bar: hello                             │                       │  │
│  │             │   6 metas:                                     │                       │  │
│  │             │   7     py_modules:                            │                       │  │
│  │             │   8         - executor.py                      │                       │  │
│  │             │   9                                            │                       │  │
│  │             ╰────────────────────────────────────────────────╯                       │  │
│  │   Docker…   The Dockerfile describes how this executor will be built.                │  │
│  │   execut…   The main logic file of the Executor.                                     │  │
│  │   manife…   Metadata for the Executor, for better appeal on Jina Hub.                │  │
│  │                                                                                      │  │
│  │               Field   Description                                                    │  │
│  │              ────────────────────────────────────────────────────────────────────    │  │
│  │               name    Human-readable title of the Executor                           │  │
│  │               desc…   Human-readable description of the Executor                     │  │
│  │               url     URL to find more information on the Executor (e.g. GitHub…     │  │
│  │               keyw…   Keywords that help user find the Executor                      │  │
│  │                                                                                      │  │
│  │   README…   A usage guide of the Executor.                                           │  │
│  │   requir…   The Python dependencies of the Executor.                                 │  │
│  │                                                                                      │  │
│  ╰──────────────────────────────────────────────────────────────────────────────────────╯  │
│  ╭────────────────────────────── 3. Share it to Jina Hub ───────────────────────────────╮  │
│  │   1 jina hub push /home/ubuntu/SentenceEncoder                                       │  │
│  ╰──────────────────────────────────────────────────────────────────────────────────────╯  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯

```

</details>

Once this is done, let's move to the newly created Executor directory:
```bash
cd SentenceEncoder
```

Let's continue by specifying our requirements in `requirements.txt` file

```text
sentence-transformers==2.0.0
```

and installing them using

```bash
pip install -r requirements.txt
```

```{admonition} Do I need to install CUDA?
:class: info

All machine learning frameworks rely on CUDA for running on GPU. However, whether you
need CUDA installed on your system or not depends on the framework that you are using.

In this tutorial, we are using PyTorch framework, which already includes the necessary
CUDA binaries in its distribution. However, other frameworks, such as Tensorflow, require
you to install CUDA yourself.
```

```{admonition} Install only what you need
:class: tip

In this example we are installing the GPU-enabled version of PyTorch, which is the default
version when installing from PyPI. However, if you know that you only need to use your
executor on CPU, you can save a lot of space (100s of MBs, or even GBs) by installing
CPU-only versions of your requirements. This translates into faster start-up times
when using Docker containers.

In our case, we could change the `requirements.txt` file to install a CPU-only version
of PyTorch like this

:::text
-f https://download.pytorch.org/whl/torch_stable.html
sentence-transformers
torch==1.9.0+cpu
:::
```

Now let's fill the `executor.py` file with the actual code of our Executor

```{code-block} python
---
emphasize-lines: 16
---
from docarray import Document, DocumentArray
from jina import Executor, requests
from sentence_transformers import SentenceTransformer
import torch


class SentenceEncoder(Executor):
    """A simple sentence encoder that can be run on a CPU or a GPU

    :param device: The pytorch device that the model is on, e.g. 'cpu', 'cuda', 'cuda:1'
    """

    def __init__(self, device: str = 'cpu', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        self.model.to(device)  # Move the model to device

    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        """Add text-based embeddings to all documents"""
        with torch.inference_mode():
            embeddings = self.model.encode(docs.texts, batch_size=32)
        docs.embeddings = embeddings
```

Here all the device-specific magic happens on the two highlighted lines - when we create the
`SentenceEncoder` class instance we pass it the device, and then we move the PyTorch
model to our device. These are the exact same steps that you would use in a standalone Python
script as well.

To see how we would pass the device we want the Executor to use,
let's create another file - `main.py`, which will demonstrate the usage of this
encoder by encoding 10 thousand text documents.

```python
from docarray import Document
from jina import Flow

from executor import SentenceEncoder


def generate_docs():
    for _ in range(10_000):
        yield Document(
            text='Using a GPU allows you to significantly speed up encoding.'
        )


f = Flow().add(uses=SentenceEncoder, uses_with={'device': 'cpu'})
with f:
    f.post(on='/encode', inputs=generate_docs, show_progress=True, request_size=32)
```

## Running on GPU and CPU locally

Let's try it out by running the same code on CPU and GPU, so we can observe the speedup we can achieve.

To toggle between the two, simply set your device type to `'cuda'`, and your GPU will take over the work:

```diff
+ f = Flow().add(uses=SentenceEncoder, uses_with={'device': 'cuda'})
- f = Flow().add(uses=SentenceEncoder, uses_with={'device': 'cpu'})
```

Then, run the script:

```bash
python main.py
```


And compare the results

````{tab} CPU 

```console
      executor0@26554[L]:ready and listening
        gateway@26554[L]:ready and listening
           Flow@26554[I]:🎉 Flow is ready to use!
        🔗 Protocol:            GRPC
        🏠 Local access:        0.0.0.0:56969
        🔒 Private network:     172.31.39.70:56969
        🌐 Public address:      52.59.231.246:56969
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━ 0:00:20 15.1 step/s 314 steps done in 20 seconds
```

````

````{tab} GPU 

```console
      executor0@21032[L]:ready and listening
        gateway@21032[L]:ready and listening
           Flow@21032[I]:🎉 Flow is ready to use!
        🔗 Protocol:            GRPC
        🏠 Local access:        0.0.0.0:54255
        🔒 Private network:     172.31.39.70:54255
        🌐 Public address:      52.59.231.246:54255
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━ 0:00:03 90.9 step/s 314 steps done in 3 seconds
```

````
Running this code on a `g4dn.xlarge` AWS instance with a single NVIDIA T4 GPU attached, we can see that the embedding
time can be decreased from 20s to 3s by running on GPU.
That is more than a **6x speedup!** And that's not even the best we can do - if we increase the batch size to max out the GPU's memory we would get even larger speedups. But such optimizations are beyond the scope of this tutorial.

```{admonition} Note
:class: note

You have probably noticed that there was a delay (about 3 seconds) when creating the Flow.
This occured because the weights of our model needed to be transfered from CPU to GPU when we
initialized the Executor. However, this action only occurs once in the lifetime of the Executor,
so for most use cases this is not something we would worry about.
```

## Using GPU in a container

```{admonition} Using your GPU inside a container
:class: tip

For this part of the tutorial, you need `nvidia-container-toolkit` installed on your machine.
If you haven't installed that already, you can find an installation guide [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
```

When you'll be using your Executor in production you will most likely want to put it in a Docker container, to provide proper environment isolation and to be able to use it easily on any device.

Using GPU-enabled Executors in this case is no harder than using them locally. In this case we don't even need to modify the default `Dockerfile`.

```{admonition} Choosing the right base image

In our case we are using the default `jinaai/jina:latest` base image. However, parallel to the comments about having to install CUDA locally, you might need to use a different base image, depending on the framework you are using.

If you need to have CUDA installed in the image, you usually have two options: either you take the `nvidia/cuda` for the base image, or you take the official GPU-enabled image of the framework you are using, for example, `tensorflow/tensorflow:2.6.0-gpu`.
```

The other file we care about in this case is `config.yml`, and here the default version works as well. So let's build the Docker image

```bash
docker build -t sentence-encoder .
```

You can run the container to quickly check that everything is working well

```bash
docker run sentence-encoder
```

Now, let's use the Docker version of our encoder with the GPU. If you've dealt with GPUs in containers before, you probably remember that to use a GPU inside the container you need to pass `--gpus all` option to the `docker run` command. And Jina enables you to do just that.

Here's how we need to modify our `main.py` script to use a GPU-base containerized Executor

```{code-block} python
---
emphasize-lines: 12
---
from docarray import Document, DocumentArray
from jina import Flow

from executor import SentenceEncoder

def generate_docs():
    for _ in range(10000):
        yield Document(
            text='Using a GPU enables you to significantly speed up encoding'
        )

f = Flow().add(
    uses='docker://sentence-encoder', uses_with={'device': 'cuda'}, gpus='all'
)
with f:
    f.post(on='/encode', inputs=generate_docs, show_progress=True, request_size=32)
```

If we run this with `python main.py`, we'll get the same output as before, except that now we'll also get the output from the Docker container.

You may notice that every time we start the Executor, the transformer model gets downloaded again. To speed this up, we would want the encoder to load the model from a file which we have pre-downloaded to our disk.

We can do this with Docker volumes - Jina will simply pass the argument to the Docker container. Here's how we modify the `main.py` to allow that

```python
f = Flow().add(
    uses='docker://sentence-encoder',
    uses_with={'device': 'cuda'},
    gpus='all',
    # This has to be an absolute path, replace /home/ubuntu with your home directory
    volumes="/home/ubuntu/.cache:/root/.cache",
)
```

Here we mounted the `~/.cache` directory, because this is where pre-built transformer models are saved in our case. But this could also be any custom directory - depends on the Python package you are using, and how you specify the model loading path.

Now, if we run `python main.py` again you can see that no downloading happens inside the container, and that the encoding starts faster.

## Using GPU with Hub Executors

We now saw how to use GPU with our Executor locally, and when using it in a Docker container. What about when we use Executors from Jina Hub, is there any difference?

Nope! Not only that, many of the Executors on Jina Hub already come with a GPU-enabled version pre-built, usually under the `gpu` tag (see [Jina Hub tags](hub_tags)). Let's modify our example to use the pre-built `TransformerTorchEncoder` from Jina Hub

```diff
f = Flow().add(
-   uses='docker://sentence-encoder',
+   uses='jinahub+docker://TransformerTorchEncoder/latest-gpu',
    uses_with={'device': 'cuda'},
    gpus='all',
    # This has to be an absolute path, replace /home/ubuntu with your home directory
    volumes="/home/ubuntu/.cache:/root/.cache"
)
```

You'll see that the first time you run the script, downloading the Docker image will take some time - GPU images are large! But after that, everything will work just as it did with your local Docker image, out of the box.

```{admonition} Important
:class: important

When using GPU encoders from Jina Hub, always use `jinahub+docker://`, and not `jinahub://`. As discussed above, these encoders might need CUDA installed (or other system dependencies), and installing that properly can be tricky. For that reason, you should prefer using Docker images, which already come with all these dependencies pre-installed.
```


## Conclusion

Let's recap what we saw in this tutorial:

1. Using Executors on a GPU locally is no different than using GPU in a standalone script. You can pass the device you want your Executor to use in the initialization.
2. To use an Executor on a GPU inside a Docker container, make sure to pass `gpus='all'`
3. Use volumes (bind mounts), so you don't have to download large files each time you start the Executor
4. You can use GPU with Executors from Jina Hub, just make sure to use the Executor with the `gpu` tag

And when you start building your own Executor, always remember to check what system requirements (CUDA and similar) are needed, and install them locally (and in the `Dockerfile`) accordingly

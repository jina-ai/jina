# Run Executors on GPU

```{article-info}
:avatar: avatars/tadej.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Tadej @ Jina AI
:date: Sept. 1, 2021
```

This tutorial will show you how to use an Executor on a GPU, both locally and in a
Docker container. You will also learn how to use GPU with pre-built Hub executors.

Using a GPU allows you to significantly speed up encoding for most deep learning models,
reducing response latency by anything from 5 to 100 times, depending on the model used and 
inputs. 

Jina enables you to use GPUs like you normally would in a Python script, or in a Docker 
container - it does not impose any additional requirements or configuration.

```{admonition} Important
:class: important

This tutorial assumes you are already familiar with basic Jina concepts, such as Document, Executor, and Flow. Some knowledge of the [Hub](../advanced/hub/index) is also needed for the last part of the tutorial.

If you're not yet familiar with these concepts, first read the [Basic Concepts](../fundamentals/concepts) and related documentation, and return to this tutorial once you feel comfortable performing baisc operations in Jina.
```

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

## Setting up the executor

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
this one (we will need it in the next section). Here's how this prompt dialogue should
look like in the end

![jina hub new](../_static/hub_new_gpu.png)


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
emphasize-lines: 16, 17
---
from typing import Optional

import torch
from jina import DocumentArray, Executor, requests
from sentence_transformers import SentenceTransformer


class SentenceEncoder(Executor):
    """A simple sentence encoder that can be run on a CPU or a GPU

    :param device: The pytorch device that the model is on, e.g. 'cpu', 'cuda', 'cuda:1'
    """

    def __init__(self, device: str = 'cpu', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        self.model.to(device)  # Move the model to device

    @requests
    def encode(self, docs: Optional[DocumentArray], **kwargs):
        """Add text-based embeddings to all documents"""
        texts = docs.get_attributes("text")
        with torch.no_grad():
            embeddings = self.model.encode(texts, batch_size=32)

        for doc, embedding in zip(docs, embeddings):
            doc.embedding = embedding
```

Here all the device-specific magic happens on the two highlighted lines - when we create the
`SentenceEncoder` class instance we pass it the device, and then we move the PyTorch
model to our device. These are the exact same steps that you would use in a standalone Python
script as well.

To see how we would pass the device we want the Executor to use,
let's create another file - `main.py`, which will demonstrate the usage of this
encoder by encoding 10 thousand text documents.

```python
from jina import Document, Flow

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

Let's try it out by running

```bash
python main.py
```
```console
      executor0@26554[L]:ready and listening
        gateway@26554[L]:ready and listening
           Flow@26554[I]:🎉 Flow is ready to use!
        🔗 Protocol:            GRPC
        🏠 Local access:        0.0.0.0:56969
        🔒 Private network:     172.31.39.70:56969
        🌐 Public address:      52.59.231.246:56969
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━ 0:00:22 13.8 step/s 314 steps done in 22 seconds
```

## Using GPU locally

By now you can already see how easy it is to use the encoder on a GPU - simply set the device on initialization to `'cuda'`

```diff
+ f = Flow().add(uses=SentenceEncoder, uses_with={'device': 'cuda'})
- f = Flow().add(uses=SentenceEncoder, uses_with={'device': 'cpu'})
```

Let's see how much faster the GPU is, compared to CPU. The following
comparison was made on `g4dn.xlarge` AWS instance, which has a single NVIDIA T4 GPU attached.

First, we need to make sure that the encoder is using the GPU - change the `'device'` parameter in `main.py`, as shown in the snippet above. With that done, let's run the benchmark again
```python
python main.py
```
```console
      executor0@21032[L]:ready and listening
        gateway@21032[L]:ready and listening
           Flow@21032[I]:🎉 Flow is ready to use!
        🔗 Protocol:            GRPC
        🏠 Local access:        0.0.0.0:54255
        🔒 Private network:     172.31.39.70:54255
        🌐 Public address:      52.59.231.246:54255
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━ 0:00:02 104.9 step/s 314 steps done in 2 seconds
```

We can see that we got over 7x speedup! And that's not even the best we can do - if we increase the batch size to max out the GPU's memory we would get even larger speedups. But such optimizations are beyond the scope of this tutorial.

```{admonition} Note
:class: note

You have probably noticed that there was a delay (about 3 seconds) when creating the Flow.
This occured because the weights of our model needed to be transfered from CPU to GPU when we
initialized the Executor. However, this action only occurs once in the lifetime of the Executor,
so for most use cases this is not something we would worry about.
```

## Using GPU in a container

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

Now, let's use the Docker version of our encoder with the GPU. If you've dealt with GPUs in containers before, you probably remember that to use a GPU insite the container you need to pass `--gpus all` option to the `docker run` command. And Jina enables you to do just that.

Here's how we need to modify our `main.py` script to use a GPU-base containerized Executor

```{code-block} python
---
emphasize-lines: 12
---
from jina import Document, DocumentArray, Flow

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
+   uses='jinahub+docker://TransformerTorchEncoder/gpu',
    uses_with={'device': 'cuda'},
    gpus='all',
    # This has to be an absolute path, replace /home/ubuntu with your home directory
    volumes="/home/ubuntu/.cache:/root/.cache",
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

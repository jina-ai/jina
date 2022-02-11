# Dockerize your Executor

Once you have understood what an `Executor` is and how it can be used inside a `Flow`, you may be interested om how to wrap this Executor into a container
so that you can isolate its dependencies and make it ready to run in the cloud or in Kubernetes.

One option is to leverage {ref}`Jina Hub <hub/index>` infrastructure to make sure your Executor can run as a container.

However, you can build a `docker` image yourself and use it as any other Executor. There are some requirements on how this image needs to be built.

The main requirements are:

- Jina must be installed inside the image
- Jina CLI command to start executor should be the default entrypoint

## Prerequisites

To be able to understand how a Container image is built for an Executor, understanding of [docker](https://docs.docker.com/) and how to write 
a [Dockerfile](https://docs.docker.com/engine/reference/builder/) to build an image.

Also, to follow the explanation and the example it is needed to have `docker` installed locally.


## Jina installed in the Image

It is strictly needed for Jina to be installed inside the docker image. This can be achieved in 2 ways.

- Use a [Jina based image](https://hub.docker.com/r/jinaai/jina) as the base image in your Dockerfile. It will make sure that everything needed for Jina
to run the Executor is installed.

```dockerfile
FROM jinaai/jina:3.0-py37-perf
```

- Simply install Jina as any other Python package. You can make sure Jina is listed as a requirement or that `pip install jina` is a command part of the image building process.  

```dockerfile
RUN pip install jina==3.0
```

## Jina Executor CLI as entrypoint

When a containerized Executor is run inside a Flow, what Jina does under the hood is to basically do `docker run` with some extra arguments. 

This means that Jina assumes that what runs inside the `container` is the same as it would run in a regular OS process. Therefore, you need to make sure that
the basic entrypoint of the `image` calls `jina executor` {ref}`CLI <../api/cli>` command.

```dockerfile
ENTRYPOINT ["jina", "executor", "--uses", "PATH_TO_YOUR_EXECUTOR_CONFIGURATION"]
```

## Example

Here we will show how to build a basic executor with a dependency on another external package.


### Write your Executor

Let's say we have our executor in a single python file called `my_executor.py`

```python
import torch # Our Executor has dependency on torch
from jina import Executor, requests

class ContainerizedEncoder(Executor):

   @requests
   def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'This Document is embedded by ContainerizedEncoder'
            doc.embedding = torch.randn(10)
```

### Write your Executor yaml file

We need to write the YAML configuration of the Executor to be put inside the Docker image. We will write it under `config.yml`

```yaml
jtype: ContainerizedEncoder
metas:
  py_modules:
    - my_executor.py
```

### Write your requirements.txt

In this case, our Executor has only one requirement besides Jina, `torch`.

So we can write a `requirements.txt` file:

```requirements.txt
torch
```

### Write a Dockerfile

The last step is to write a `Dockerfile`

```dockerfile
FROM jinaai/jina:3.0-py37-perf

# make sure the files are copied into the image
COPY . /executor_root/

WORKDIR /executor_root

RUN pip install -r requirements.txt

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
```

### Build the image

At this point we have a folder structure looking like this:

```
.
├── my_executor.py
└── requirements.txt
└── config.yml
└── Dockerfile
```

We just need to build the image:

```bash
docker build -t my_containerized_executor .
```

Once the build is successful, you should see under `docker images`

```console
REPOSITORY                       TAG                IMAGE ID       CREATED          SIZE
my_containerized_executor        latest             5cead0161cb5   13 seconds ago   2.21GB
```

### Use it

```python
from docarray import DocumentArray, Document
from jina import Flow

f = Flow().add(uses='docker://my_containerized_executor')

with f:
    returned_docs = f.post(on='/', inputs=DocumentArray([Document()]), return_results=True)

for doc in returned_docs:
    print(f'Document returned with text: "{doc.text}"')
    print(f'Document embedding of shape {doc.embedding.shape}')
```

```console
Document returned with text: "This Document is embedded by ContainerizedEncoder"
Document embedding of shape torch.Size([10])
```

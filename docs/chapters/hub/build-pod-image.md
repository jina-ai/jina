# Build Your Pod into a Docker Image

## Goal

Instead of 
```bash
jina pod --uses hub/example/mwu_encoder.yml --port-in 55555 --port-out 55556
```

After this tutorial, you can use the Pod image via:
```bash
docker run jinaai/hub.examples.mwu_encoder --port-in 55555 --port-out 55556
```

...or use the Pod image in the Flow API:
```python
from jina.flow import Flow

f = (Flow()
        .add(name='my-encoder', image='jinaai/hub.examples.mwu_encoder', port_in=55555, port_out=55556)
        .add(name='my-indexer', uses='indexer.yml'))
```

... or use the Pod image via Jina CLI
```bash
jina pod --uses jinaai/hub.examples.mwu_encoder --port-in 55555 --port-out 55556
```

More information about [the usage can be found here](./use-your-pod.html#use-your-pod-image).


## Why?

So you have implemented an awesome executor and want to reuse it in another Jina application, or share it with people in the world. Kind as you are, you want to offer people a ready-to-use interface without hassling them to repeat all steps and pitfalls you have done. The best way is thus to pack everything (python file, YAML config, pre-trained data, dependencies) into a container image and use Jina as the entry point. You can also annotate your image with some meta information to facilitate the search, archive and classification.

Here are a list of reasons that may motivate you to build a Pod image:

- You want to use one of the built-in executor (e.g. pytorch-based) and you don't want to install pytorch dependencies on the host.
- You modify or write a new executor and want to reuse it in another project, without touching [`jina-ai/jina`](https://github.com/jina-ai/jina/).
- You customize the driver and want to reuse it in another project, without touching [`jina-ai/jina`](https://github.com/jina-ai/jina/).
- You have a self-built library optimized for your architecture (e.g. tensorflow/numpy on GPU/CPU/x64/arm64), and you want this specific Pod to benefit from it.
- Your awesome executor requires certain Linux headers that can only be installed via `apt` or `yum`, but you don't have `sudo` on the host.
- You executor relies on a pretrained model, you want to include this 100MB file into the image so that people don't need to download it again.  
- You use Kubernetes or Docker Swarm and this orchestration framework requires each microservice to run as a Docker container.
- You are using Jina on the cloud and you want to deploy an immutable Pod and version control it.
- You have figured out a set of parameters that works best for an executor, you want to write it down in a YAML config and share it to others.
- You are debugging, doing try-and-error on exploring new packages, and you don't want ruin your local dev environments. 


## What Should be in the Image?

Typically, the following files are packed into the container image:

| File             | Descriptions                                                                                        |
|------------------|-----------------------------------------------------------------------------------------------------|
| `Dockerfile`     | describes the dependency setup and expose the entry point;                                          |
| `build.args`     | metadata of the image, author, tags, etc. help the Hub to index and classify your image             |
| `*.py`           | describes the executor logic written in Python, if applicable;                                      |
| `*.yml`          | a YAML file describes the executor arguments and configs, if you want users to use your config;     |
| Other data files | may be required to run the executor, e.g. pre-trained model, fine-tuned model, home-made data.      |

Except `Dockerfile`, all others are optional to build a valid Pod image depending on your case. `build.args` is only required when you want to [upload your image to Jina Hub](./publish-your-pod-image.html#publish-your-pod-image-to-jina-hub).
    
## Step-by-Step Example

In this example, we consider the scenario where we creates a new executor and want to reuse it in another project, without touching [`jina-ai/jina`](https://github.com/jina-ai/jina/). All files required in this guide is available at [`hub/examples/mwu_encoder`](/hub/examples/mwu_encoder).

### 1. Write Your Executor and Config

We write a new dummy encoder named `MWUEncoder` in [`mwu_encoder.py`](hub/examples/mwu_encoder/mwu_encoder.py) which encodes any input into a random 3-dimensional vector. This encoder has a dummy parameter `greetings` which prints a greeting message on start and on every encode. In [`mwu_encoder.yml`](hub/examples/mwu_encoder/mwu_encoder.yml), the `metas.py_modules` tells Jina to load the class of this executor from `mwu_encoder.py`.

```yaml
!MWUEncoder
with:
  greetings: im from internal yaml!
metas:
  name: my-mwu-encoder
  py_modules: mwu_encoder.py
  workspace: ./
```

The documentations of the YAML syntax [can be found at here](../yaml/yaml.html#executor-yaml-syntax). 

### 2. Write a 3-Line `Dockerfile`

The `Dockerfile` in this example is as simple as three lines, 

```Dockerfile
FROM jinaai/jina:devel

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--uses", "mwu_encoder.yml"]
```

Let's now look at these three lines one by one.

>
```Dockerfile
FROM jinaai/jina:devel
``` 

In the first line, we choose `jinaai/jina:devel` as [the base image](https://docs.docker.com/glossary/#base-image), which corresponds to the latest master of [`jina-ai/jina`](https://github.com/jina-ai/jina). But of course you are free to use others, e.g. `tensorflow/tensorflow:nightly-gpu-jupyter`. 

In practice, whether to use Jina base image depends on the dependencies you would like to introduce. For example, someone provides a hard-to-compile package as a Docker image, much harder than compiling/installing Jina itself. In this case, you may want to use this image as the base image to save some troubles. But don't forget to install Python >=3.7 (if not included) and Jina afterwards, e.g.

> 
```Dockerfile
FROM awesome-gpu-optimized-kit

RUN pip install jina --no-cache-dir --compile
```

The ways of [installing Jina can be at found here](https://github.com/jina-ai/jina#run-without-docker).

In this example, our dummy `MWUEncoder` only requires Jina and does not need any third-party framework. Thus, `jinaai/jina:devel` is used.

```Dockerfile
ADD *.py mwu_encoder.yml ./
```

The second step is to add *all* necessary files to the image. Typically, Python codes, YAML config and some data files.

In this example, our dummy `MWUEncoder` does not require extra data files.

> 
```Dockerfile
ENTRYPOINT ["jina", "pod", "--uses", "mwu_encoder.yml"]
``` 

The last step is to specify the entrypoint of this image, usually via `jina pod`.

In this example, we set `mwu_encoder.yml` as a default YAML config. So if the user later run

```bash
docker run jinaai/hub.examples.mwu_encoder
```
 
It is equal to:
```bash
jina pod --uses hub/example/mwu_encoder.yml
```

Any followed key-value arguments after `docker run jinaai/hub.examples.mwu_encoder` will be passed to `jina pod`. For example,

```bash
docker run jinaai/hub.examples.mwu_encoder --port-in 55555 --port-out 55556
```
 
It is equal to:
```bash
jina pod --uses hub/example/mwu_encoder.yml --port-in 55555 --port-out 55556
```

One can also override the internal YAML config by giving an out-of-docker external YAML config via:

```bash
docker run -v $(pwd)/hub/example/mwu_encoder_ext.yml:/ext.yml jinaai/hub.examples.mwu_encoder --uses /ext.yml
```


### 3. Build the Pod Image

Now you can build the Pod image via `docker build`:

```bash
cd hub/example
docker build -t jinaai/hub.examples.mwu_encoder .
```

Depending on whether you want to use the latest Jina image, you may first pull it via `docker pull jinaai/jina:devel` before the build. For the sake of immutability, `docker build` will not automatically pull the latest image for you.

Congratulations! You can now re-use this Pod image how ever you want.
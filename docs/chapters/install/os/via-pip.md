# Install Jina via `pip`

If you prefer to run Jina natively on your host, please make sure you have Python >= 3.7 installed.

## Install from PyPi

On Linux/Mac, simply run:
 
```bash
pip install jina
```

## Install from the Master Branch

If you want to keep track of the master branch of our development repository:

```bash
pip install git+https://github.com/jina-ai/jina.git
```

Be aware that the master branch may not be stable. We only recommend this branch for testing new features.

## Install from Your Local Fork/Clone

If you are a developer and want to test your changes on-the-fly: 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e .
``` 

In the dev mode, if you later switch to a different method of Jina installation, remember to first uninstall the version you edited:

```bash
pip uninstall $(basename $(find . -name '*.egg-info') .egg-info)
```

## Cherry-Pick Extra Dependencies

Jina requires only five dependencies `numpy`, `pyzmq`, `protobuf`, `grpcio` and `pyyaml`. No third-party pre-trained models, deep learning/NLP/CV packages will be installed. 

However, some Executors may require extra dependencies. The full table of these extra dependencies can be found in `extra-requirements.txt`. You can cherry-pick what you want to install, e.g.

```bash
pip install "jina[nlp+cv]"
``` 

This will install all dependencies tagged with `nlp` or `cv`.

Though not recommended, you can install Jina with full dependencies via:

```bash
pip install "jina[all]"
``` 

### To Install Cherry-Picked Dependencies From the Master Branch

```bash
pip install "git+https://github.com/jina-ai/jina.git#egg=jina[http]" 
```

### Extra Dependencies Explained

These are the extra dependencies used by Jina:

| PyPi Name | Required by | Description | Compatibility
|---|---|---|---|
|`scipy>=0.4.1`| `numeric`, `index` | `Scientific Library for Python. Required for similarity measure computation and required for many other extra packages (tensorflow, paddlehub ...)` | `tensorflow>=2.0.0 requires scipy>=1.4.1, while paddlepaddle<1.8.1 require scipy<=1.3.1.`
|`flask, flask-cors`| `http`, `sse` | `A simple framework for building complex web applications, used for logging server and exposing REST API.` |
|`fluent-logger` | `logging` | `fluent-logger-python is a Python library, to record the events from Python application.` |
|`nmslib` | `index` | `Non-Metric Space Library (NMSLIB) is an efficient cross-platform similarity search library` | 
|`docker` | `network` | `A Python library for the Docker Engine API` | `See https://docs.docker.com/engine/api/ for compatibility with docker engine versions.`
|`torch>=1.0.0` | `framework` | `Tensors and Dynamic neural networks in Python with strong GPU acceleration. Enables several image encoders, object detection crafters and transformers models` | `It imposes compatibility restrictions with torchvision (https://pypi.org/project/torchvision/).`
|`transformers>=2.6.0` | `nlp` | ` Repository of pre-trained NLP Transformer models` | `Some flair versions impose some requirements on the transformer version required. For proper padding to work, version 2.6.0 is required as minimmum version.`
|`flair` | `nlp` | `A very simple framework for state-of-the-art NLP` | `It imposes restrictions on torch and transformers version compatibility.`
|`paddlepaddle` | `framework` | `Parallel Distributed Deep Learning` | `It imposes restrictions on scipy version and is required for paddlehub models.`
|`paddlehub` | `framework` | `A toolkit for managing pretrained models of PaddlePaddle` | `Requires paddlepaddle.`
|`tensorflow>=2.0` | `framework` | `TensorFlow is an open source machine learning framework for everyone.`
|`tensorflow-hub` | `framework` | `TensorFlow Hub is a library to foster the publication, discovery, and consumption of reusable parts of machine learning models.`
|`torchvision>=0.3.0` | `framework, cv` | `image and video datasets and models for torch deep learning` | `Make sure that the models you want to use ara available at your installed torchvision version.`
|`Pillow` | `cv` | ` Python Imaging Library`
|`onnx` | `framework` | `Open Neural Network Exchange.` 
|`onnxruntime` | `framework` | `ONNX Runtime Python bindings.` 
|`annoy` | `index` | `Approximate Nearest Neighbors in C++/Python optimized for memory usage and loading/saving to disk.`
|`sklearn` | `numeric` | `A set of python modules for machine learning and data mining. Used for a variety of numeric encoders.`
|`plyvel` | `index` | `fast and feature-rich Python interface to LevelDB. Enables the use of LevelDB as a Key-Value indexer.`
|`jieba` | `nlp` | `Chinese Words Segmentation Utilities`
|`lz4` | `optimization, network` | `LZ4 Bindings for Python. Enables compression to send large messages.`
|`gevent` | `http` | `Coroutine-based network library`
|`python-magic` | `http` | `File type identification using libmagic. Used to identify document request type.`
|`pymilvus` | `index` | ` Python Sdk for Milvus. Enables the usage of Milvus DB as vector indexer as a client.`
|`librosa` | `audio` | `Python module for audio and music processing.`
|`deepsegment` | `nlp` | `Sentence Segmentation with sequence tagging.`
|`ngt` | `index` | `Neighborhood Graph and Tree for Indexing High-dimensional Data.`
|`uvloop` | `òptimization` | `Fast implementation of asyncio event loop on top of libuv.`

## On Windows

Currently we do not support native python on Windows.

If you are a Windows user, one workaround is to [run Jina on Windows Subsystem for Linux](on-wsl.md) or [run Jina in a Docker container](via-docker.md). If you manage to run Jina on Windows after some tweaks, please submit your changes [here](https://github.com/jina-ai/jina/issues/new).

## Other OSes
Please refer to [run Jina in a Docker container](via-docker.md). If you manage to run Jina on other OSes after some tweaks, please submit your changes [here](https://github.com/jina-ai/jina/issues/new).

# Upgrade Jina

If you have a previously installed version of Jina, you can upgrade it by running:

```bash
pip install -U jina
```

For Docker users: 

```bash
docker pull jinaai/jina
```

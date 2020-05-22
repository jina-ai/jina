# Install Jina via `pip`

If you prefer run Jina natively on the host, please make sure you have Python >= 3.7 installed on the host.

## Install from PyPi

On Linux/Mac, simply do:
 
```bash
pip install jina
```

## Install from the Master Branch

If you want to keep track on the master of our development repository:

```bash
pip install git+https://github.com/jina-ai/jina.git
```

## Install from Your Local Folk/Clone

If you are a developer and want to test your changes on-the-fly: 

```bash
git clone https://github.com/jina-ai/jina
cd jina && pip install -e .
``` 

In the dev mode, if you later switch to the other ways of Jina installation, remember to first uninstall the editable version from the system:
  ```bash
  pip uninstall $(basename $(find . -name '*.egg-info') .egg-info)
  ```

## Cherry Pick Extra Dependencies

Jina only requires five dependencies `numpy`, `pyzmq`, `protobuf`, `grpcio` and `ruamel.yaml`. No third-party pretrained models, deep learning/NLP/CV packages will be installed. 

Some of the Executors may require extra dependencies. The full table of the extra dependencies can be found in `extra-requirements.txt`. You can cherry-pick what you want to install, e.g.

```bash
pip install "jina[nlp+cv]"
``` 

This will install all dependencies tagged with `nlp` or `cv`.

Though not recommended, you can install Jina with full dependencies via:

```bash
pip install "jina[all]"
``` 

### To install cherry-picked dependencies from master branch

```bash
pip install "git+https://github.com/jina-ai/jina.git#egg=jina[http]" 
```


## Install Jina on Raspberry Pi and other Linux Systems

On Raspbian or other Linux systems, you can also install Jina via:

```bash
pip install jina
```

On some Linux systems, PyPi may not provide the wheels on that OS. In this case, you may want to pre-install some dependencies via `apt`/`yum` not via `pip`. Since the packages on `apt`/`yum` are often pre-compiled and require much less time to install. Fortunately Jina have minimal dependencies and their corresponding `apt`/`yum` packages are listed as follows:

| PyPi Name | Debian Package Name | Alpine Package Name |
|---|---|---|
|`numpy`| `python3-numpy` | `py3-numpy` |
|`pyzmq>=17.1.0`| `python3-zmq` | `py3-pyzmq`|
|`protobuf`| `python3-protobuf`| `py3-protobuf`|
|`grpcio`| `python3-grpcio`| `grpc` |
|`ruamel.yaml>=0.15.89`| `python3-ruamel.yaml`| `py3-ruamel.yaml`|

If you can have Docker installed on your Linux, then an easier way is probably [run Jina with Docker container](via-docker.md).

## On Windows and Other OS

Currently we do not support Windows.

If you are a Windows user, one workaround is to [use Jina with Docker container](via-docker.md). If you manage to run Jina on Windows after some tweaks, welcome to submit your changes [to here](https://github.com/jina-ai/jina/issues/new).

# Install Jina on Raspberry Pi and other Linux Systems


On Raspbian or other Linux systems with Python >= 3.7 installed, you can simply install Jina via:

```bash
pip install jina
```

On some Linux systems, PyPi may not provide the wheels on that OS. In this case, you may want to pre-install some dependencies via `apt`/`yum` not via `pip`. Since the packages on `apt`/`yum` are often pre-compiled and require much less time to install. Fortunately Jina have minimal dependencies and their corresponding `apt`/`yum` packages are:

| PyPi Name | Linux Package Name | Alpine Package Name |
|---|---|---|
|`numpy`| `python3-numpy` | `py3-numpy` |
|`pyzmq>=17.1.0`| `python3-zmq` | `py3-pyzmq`|
|`protobuf`| `python3-protobuf`| `py3-protobuf`|
|`grpcio`| `python3-grpcio`| `grpc` |
|`ruamel.yaml>=0.15.89`| `python3-ruamel.yaml`| `py3-ruamel.yaml`|

If you can have Docker installed on your Linux, then an easier way is probably [run Jina with Docker container](via-docker.md).

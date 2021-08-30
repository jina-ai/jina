# Install

Standard install enables the full features of Jina. 

````{tab} via PyPI
```shell
pip install -U jina
```
````
````{tab} via Docker
```shell
docker run jinaai/jina:latest
```
````

## More install options

Version identifiers [are explained here](https://github.com/jina-ai/jina/blob/master/RELEASE.md). Jina can run
on [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community
to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

### Minimum

Minimum install enables basic features of Jina, but without support on HTTP, WebSocket, Docker & Hub.

Minimum install is often used when building & depolying an Executor.


````{tab} via PyPI

```shell
JINA_PIP_INSTALL_CORE=1 pip install jina
```


````

````{tab} via Docker

```shell
docker run jinaai/jina:latest
```

````

### Minimum but more performant

Same as Minimum install, but also install `uvloop` & `lz4`.


````{tab} via PyPI

```shell
JINA_PIP_INSTALL_PERF=1 pip install jina
```


````

````{tab} via Docker

```shell
docker run jinaai/jina:latest-perf
```

````


### With Daemon (JinaD)

Same as Minimum install, but also install `uvloop` & `lz4`.

```shell
pip install "jina[daemon]
```


### Full development dependencies


````{tab} via PyPI

```shell
pip install "jina[devel]
```


````

````{tab} via Docker

```shell
docker run jinaai/jina:latest-devel
```

````


### Prerelease

````{tab} via PyPI

```shell
pip install --pre jina
```


````

````{tab} via Docker

```shell
docker run jinaai/jina:master
```

````





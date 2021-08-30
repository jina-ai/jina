Install Jina
============

- via PyPI: `pip install -U jina`
- via Docker: `docker run jinaai/jina:latest`

<details>
<summary>More installation options</summary>

| On x86/64, arm64/v6/v7 | Linux/macOS with Python 3.7/3.8/3.9 | Docker Users |
| --- | --- | --- |
| Minimum <br>(no HTTP, WebSocket, Docker support) | `JINA_PIP_INSTALL_CORE=1 pip install jina` | `docker run jinaai/jina:latest` |
| Minimum but more performant <br>(use `uvloop` & `lz4`) | `JINA_PIP_INSTALL_PERF=1 pip install jina` | `docker run jinaai/jina:latest-perf` |
| With <a href="https://api.jina.ai/daemon/">Daemon</a> | `pip install "jina[daemon]"` | [Run JinaD](.github/2.0/cookbooks/Daemon.md#run) |
| Full development dependencies | `pip install "jina[devel]"` | `docker run jinaai/jina:latest-devel` |
| Pre-release<br>(all tags above can be added)| <sub>`pip install --pre jina` | `docker run jinaai/jina:master` |


Version identifiers [are explained here](https://github.com/jina-ai/jina/blob/master/RELEASE.md). Jina can run
on [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). We welcome the community
to help us with [native Windows support](https://github.com/jina-ai/jina/issues/1252).

</details>

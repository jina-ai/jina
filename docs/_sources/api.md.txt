# Python API

To generate docs, please use:

```bash
cd docs
bash makedocs.sh local-only
```

There are four packages shipped with Jina:

- `jina`: the framework;
- `docarray`: the basic data types such as `Document`, `DocumentArray`;
- `daemon`: a simple orchestrator for Jina;
- `cli`: the command line interface for Jina.

```{toctree}
:hidden:

api/jina
api/docarray
api/daemon
api/cli
```
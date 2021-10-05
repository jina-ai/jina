(hub-cookbook)=

# Share Executors via Hub

Now you understand that `Executor` is a building block in Jina. The following questions arise naturally:

- Can I reuse my Executor in another project?
- Can I share my Executor to my colleague?
- Can I simply use others' Executor without implementing it?

Basically, something like the following:

```{figure} ../../../.github/hub-user-journey.svg
:align: center
```

**Yes!** This is exactly the purpose of Jina Hub - a marketplace for Executors. By using Hub you can pull prebuilt
Executors to dramatically reduce the effort and complexity needed in your search system, or push your own custom
Executors to share privately or publicly.

A Hub Executor is an executor that is published in Jina Hub. Such an executor can be easily used in a Flow like this:

```python
from jina import Flow

f = Flow().add(uses='jinahub+docker://MyExecutor')

with f:
    ...
``` 

## Hub architecture

The Hub architecture looks like the following:

```{figure} ../../../.github/hub-system.svg
:align: center
```

```{toctree}
:hidden:

hub-portal
create-hub-executor
push-executor
use-hub-executor
executor-best-practices
```

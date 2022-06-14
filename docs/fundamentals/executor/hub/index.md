(jina-hub)=
# Hub

```{figure} https://docs.jina.ai/_images/hub-banner.png
:width: 0 %
:scale: 0 %
```

```{figure} img/hub-banner.png
:scale: 0 %
:width: 0 %
```

Now that you understand that {class}`~jina.Executor` is a building block in Jina, the following questions may arise:

- Can I reuse my Executor in another project?
- Can I share my Executor with my colleagues?
- Can I just use someone else's Executor instead of building it myself?

Basically, something like the following:

```{figure} ../../../../.github/hub-user-journey.svg
:align: center
```

**Yes!** This is exactly the purpose of Jina Hub - a marketplace for Executors. With Hub you can pull prebuilt
Executors to dramatically reduce the effort and complexity needed in your search system, or push your own custom
Executors to share privately or publicly.

A Hub Executor is an Executor that is published in Jina Hub. Such an Executor can be easily used in a Flow:

```python
from jina import Flow

f = Flow().add(uses='jinahub+docker://MyExecutor')

with f:
    ...
``` 

## Hub architecture

The Hub architecture looks like the following:

```{figure} ../../../../.github/hub-system.svg
:align: center
```

## Environment Variables

A list of environment variables which takes effects during Jina Hub operations. e.g. `jina hub push`

### `JINA_HUB_ROOT`

**Define the place where the Executor package cache lives.** Default value is `~/.jina/hub-packages`

````{admonition} Hint
:class: hint
You don't have permissions to create a directory in the home folder sometime. This is the right time to change the value.
````

### `JINA_HUB_CACHE_DIR`

**Define the place where the cache is stored during the downloading.** The cache will be deleted after downloading. Default value is `${JINA_HUB_ROOT}/.cache`.


```{toctree}
:hidden:

hub-portal
create-hub-executor
push-executor
use-hub-executor
../../../how-to/sandbox
../../../how-to/debug-executor
executor-best-practices
```

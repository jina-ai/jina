(flow)=
# Create Flow

An empty Flow can be created via:

```python
from jina import Flow

f = Flow()
```

## Use a Flow

To use `f`, always open it as a context manager, just like you open a file. This is considered the best practice in
Jina:

```python
with f:
    ...
```

````{admonition} Note
:class: note
Flow follows a lazy construction pattern: it won't actually run until you use `with` to open it.
````

````{admonition} Warning
:class: warning
Once a Flow is open via `with`, you can send data requests to it. However, you cannot change its construction
via `.add()` any more until it leaves the `with` context.
````

````{admonition} Important
:class: important
The context exits when its inner code is finished. A Flow's context without inner code will immediately exit. To
prevent that, use `.block()` to suspend the current process.

```python
with f:
    f.block()  # block the current process
```

To terminate a blocked Flow, one can send use `threading.Event` or `multiprocessing.Event` to send the terminate signal.
The following example terminates a Flow from another process. 

```python
import multiprocessing
import time

from jina import Flow

ev = multiprocessing.Event()

def close_after_5s():
    time.sleep(5)
    ev.set()

f = Flow().add()
with f:
    t = multiprocessing.Process(target=close_after_5s)
    t.start()
    f.block(stop_event=ev)
```
````
## Visualize a Flow

```python
from jina import Flow

f = Flow().add().plot('f.svg')
```

```{figure} empty-flow.svg
:align: center
```

In Jupyter Lab/Notebook, the `Flow` object is rendered automatically without needing to call `plot()`.





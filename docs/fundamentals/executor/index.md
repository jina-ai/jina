(executor-cookbook)=
# Executor

{class}`~jina.Executor` represents a processing component in a Jina Flow. It performs a single task on a `Document` or 
`DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.


```{toctree}
:hidden:

executor-api
executor-built-in-features
executors-in-action
repository-structure
../../tutorials/gpu-executor
```

````{admonition} See Also
:class: seealso

Document, Executor, and Flow are the three fundamental concepts in Jina.

- {doc}`Document <../document/index>` is the basic data type in Jina;
- {ref}`Executor <executor>` is how Jina processes Documents;
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors.
````

````{dropdown} Design Principle of Executor

In Jina 2.0 the Executor class is generic to all categories of executors (`encoders`, `indexers`, `segmenters`,...) to
keep development simple. We do not provide subclasses of `Executor` that are specific to each category. The design
principles are (`user` here means "Executor developer"):

- **Do not surprise the user**: keep `Executor` class as Pythonic as possible. It should be as light and unintrusive as
  a `mixin` class:
    - do not customize the class constructor logic;
    - do not change its built-in interfaces `__getstate__`, `__setstate__`;
    - do not add new members to the `Executor` object unless needed.
- **Do not overpromise to the user**: do not promise features that we can hardly deliver. Trying to control the
  interface while delivering just loosely-implemented features is bad for scaling the core framework. For
  example, `save`, `load`, `on_gpu`, etc.

We want to give our users the freedom to customize their executors easily. If a user is a good Python programmer, they
should pick up `Executor` in no time. It is as simple as subclassing `Executor` and adding an endpoint.

````
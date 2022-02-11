(executor-cookbook)=
# Executor

{class}`~jina.Executor` represents a processing component in a Jina Flow. It performs a single task on a `DocumentArray`. 

You can create an Executor by extending the `Executor` class and adding logic to endpoint methods.


## Why should you use Executor?

Once you have learned `DocumentArray`, you are capable of using all its power and expressiveness to build a neural search application.
Now you need to organize your code in independent modules to be served and scaled independently as microservices.

- Executor lets the developer organize their `DocumentArray` based functions into logical entities that can share configuration state following OOP.

- Executor converts your local functions into functions that can be distributed inside a Flow.

- Using Executor inside a Flow multiple `DocumentArray` can be processed at the same time in a concurrent manner, and deployed easily in the cloud as part of a neural search application.

- They can be easily containerized and shared with your colleagues with `jina hub push/pull`

```{toctree}
:hidden:

executor-api
executor-in-flow
repository-structure
hub/index
```

````{admonition} See Also
:class: seealso

Executor, and Flow are the two fundamental concepts in Jina.

- {ref}`Executor <executor>` is how Jina processes Documents;
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors.
````
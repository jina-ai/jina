# {octicon}`book` How-To

Jina is a powerful framework for building multimodal AI services, from start to finish.

```{admonition} See Also
:class: seealso
If you are new to Jina, first check its {ref}`overview <architecture-overview>` for more background.
```

## Executor

On top of the {ref}`basics <executor-cookbook>`, the {class}`~jina.Executor` has a few more tricks up its sleeve.

\
**Scaling out**: Often, running a single Executor for a given task is just not enough. 
{ref}`This tutorial <scale-out>` covers
scaling out using Jina, including increasing throughput and partitioning data.


\
**Executors on GPU**: Machine Learning models are only as fast as the metal they run on, and for maximum performance you
want that metal to be a GPU. To run Executors on GPU and accelerate your code, see
{ref}`this tutorial <gpu-executor>`.

\
**External Executors**: Executors don't need to be tied to a specific Flow. If you want to spawn Executors on
their own, use them in various Flows, even from a different machine or from inside a Docker container, then follow along
{ref}`here <external-executor>`.


## Deployment

Once you've built your search app using Jina, you want to deploy it. Jina plays nice with your
favorite tools for the job:

\
**Docker Compose**: To learn about Jina's native support for Docker Compose, including deployment, 
check {ref}`this guide <docker-compose>`.

\
**Kubernetes**: Jina supports Kubernetes natively. Check the guide {ref}`here <kubernetes>`.


```{toctree}
:hidden:

realtime-streaming
flow-switch
scale-out
../fundamentals/clean-code
google-colab
gpu-executor
external-executor
docker-compose
kubernetes
opentelemetry
opentelemetry-migration
```

# {octicon}`book;1em;sd-text-info` How-To

Jina is a very powerful framework that can help you build distributed neural search applications, from start to finish.

```{admonition} See Also
:class: seealso
If you are completely new to Jina, you should check out its {ref}`overview <architecture-overview>` first.
You may also find the [learning portal](https://learn.jina.ai/) useful to get off the ground.
```

In order to get you started on your more ambitious projects, we compiled a list of how-to tutorials that guide you through some of Jina's more advanced features. Happy coding!

## Executor

On top of the {ref}`basics <executor-cookbook>`, `Executor` has a few more tricks up its sleeve.

\
**Scaling out**: In many scenarios, running a single Executor for a given task is just not enough. Whether you need more
throughput or to partition your data, we've got you covered. {ref}`This tutorial <scale-out>` will show you how to
easily scale out using Jina.


\
**Executors on GPU**: Machine Learning models are only as fast as the metal they run on, and for maximum performance you
want that metal to be a GPU. For a guide on how to run Executors on GPU and accelerate your code, see
{ref}`this tutorial <gpu-executor>`.

\
**External Executors**: Executors need not be tied to a specific Flow. If you want to learn how to spawn Executors on
their own, use them in various Flows, even from a different machine or from inside a Docker container, then follow along
{ref}`here <external-executor>`.


## Deployment

Once you have built your search app using Jina, naturally you want to deploy it. Luckily, Jina plays nice with your
favorite tools for the job.

\
**Docker Compose**: If you want to learn about Jina's native support for Docker Compose, including deployment, look no
further than {ref}`this guide <docker-compose>`.

\
**Kubernetes**: If your weapon of choice is Kubernetes then fear not, because it is supported by Jina natively. How you
can put that into practice you can find {ref}`here <kubernetes>`.


```{toctree}
:hidden:

../fundamentals/clean-code
async-executors
scale-out
gpu-executor
external-executor
flow-switch
docker-compose
kubernetes
monitoring
```
# Learn how to use Jina in depth

Jina is a very powerful framework that can help you build distributed neural search applications, from start to finish.

In order to get you started on your more ambitious projects, we compiled a list of how-to tutorials that guide you
through some of Jina's more advanced features. Happy coding!

## Executor

On top of the {ref}`basics <executor-cookbook>`, `Executor` has a few more tricks up its sleeve.

\
**Scaling out**: In many scenarios, running a single Executor for a given task is just not enough. Do you need more
speed in order to alleviate bottlenecks? No problem - *replicas* are here to help. Or did you accumulate a lot of data
which you want to split into partitions? We've got you covered - with the power of *sharding*.
To learn how to put both of these techniques into practice, take a look at {ref}`this tutorial <scale-out>`.



```{toctree}
:hidden:

docker-compose
kubernetes
gpu-executor
async-executor
sandbox
```
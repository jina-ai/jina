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

**Yes!** This is exactly the purpose of Jina Hub - a one-stop shop for Executors. By using Hub you can pull prebuilt Executors to dramatically reduce the effort and complexity needed in your search system, or push your own custom Executors to share privately or publicly.

The whole architecture looks like the following:

```{figure} ../../../.github/hub-system.svg
:align: center
```


```{toctree}
:hidden:

create-hub-executor
push-executor
use-hub-executor
pull-executor
practice-your-learning
executor-best-practices
```

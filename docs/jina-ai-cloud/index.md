# {octicon}`flame` Jina AI Cloud



:::::{grid} 2
:gutter: 3


::::{grid-item-card} {octicon}`package-dependents;1.5em` Explore Executor Hub
:link: ../fundamentals/executor/hub/index
:link-type: doc


Executor Hub is an Executor marketplace that allows you to share, explore and test Executors.

::::


::::{grid-item-card} {octicon}`cpu;1.5em` Deploy a Flow to JCloud
:link: ../fundamentals/jcloud/index
:link-type: doc

JCloud is a free CPU/GPU hosting platform for Jina projects.
::::


:::::


Jina AI Cloud is the **portal** and **single entrypoint** to manage **all** your Jina AI resources, including: 
- Data
  - [DocumentArray](https://docarray.jina.ai/fundamentals/documentarray/serialization/#from-to-cloud)
  - [Finetuner artifacts](https://finetuner.jina.ai/walkthrough/save-model/#save-artifact)
- [Executors](../fundamentals/executor/index.md)
- [Flows](../fundamentals/flow/index.md)
- [Apps](https://now.jina.ai)

_Manage_ in this context means: CRUD, access control, personal access tokens, and subscription.


```{admonition} Under Development
:class: danger

Jina AI Cloud is under a heavy developement. Features and user experiences may change over time. 

We are actively working on the GUI for Jina AI Cloud. You may not see the full features right now. 
```

```{toctree}
:hidden:

login
../fundamentals/executor/hub/index
../fundamentals/jcloud/index
```
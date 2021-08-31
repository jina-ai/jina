# Welcome to Jina!

Jina is a deep learning-powered search framework for building cross-/multi-modal (e.g. text, images, video, audio) search systems on the cloud. It allows you to build neural search-as-a-service in just minutes.

1. Make sure that you have Python 3.7+ installed.
2. Install Jina: ``pip install jina``
3. Run hello-world demos: ``jina hello fashion``
4. That’s it! In the next few seconds the demo will open in a new page in your browser.

## Next Steps

:::::{grid} 2
:gutter: 3


::::{grid-item-card} {octicon}`smiley;1.5em` Play 3 Hello Worlds
:link: get_started/hello-world/index
:link-type: doc

Try Jina on fashion image search, QA chatbot and multimodal search.

::::

::::{grid-item-card} {octicon}`book;1.5em` Understand Basics
:link: fundamentals/concepts
:link-type: doc

Document, Executor, and Flow are the three fundamental concepts in Jina.

::::

::::{grid-item-card} {octicon}`package-dependents;1.5em` Share Executors
:link: advanced/hub/index
:link-type: doc

Learn how to share and reuse Executors from community.

::::


::::{grid-item-card} {octicon}`workflow;1.5em`  Manage Remote Jina 
:link: advanced/daemon/index
:link-type: doc

Learn how to deploy and manage Jina on remote via a RESTful interface.
::::


::::{grid-item-card} {octicon}`thumbsup;1.5em` Clean & Efficient Code 
:link: fundamentals/clean-code
:link-type: doc

Write beautiful & lean code with Jina.
::::
:::::



```{toctree}
:caption: Get started
:hidden:

get_started/neural-search
get_started/install
get_started/hello-world/index
```

```{toctree}
:caption: Fundamentals
:hidden:

fundamentals/concepts
fundamentals/document/index
fundamentals/executor/index
fundamentals/flow/index
fundamentals/clean-code
fundamentals/practice
```


```{toctree}
:caption: Advanced
:hidden:

advanced/hub/index
advanced/daemon/index
```

```{toctree}
:caption: Developer Reference
:hidden:
:maxdepth: 1

api/jina
cli/index
proto/index
```

```{toctree}
:caption: Links
:hidden:

Showcase <https://showcase.jina.ai>
GitHub repository <https://github.com/jina-ai/jina>
Slack community <https://slack.jina.ai>
Company website <https://jina.ai>

```

{ref}`genindex` 

{ref}`modindex`


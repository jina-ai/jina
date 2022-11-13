(jcloud)=
# Jina AI Cloud Hosting


```{toctree}
:hidden:

yaml-spec
```

```{figure} https://docs.jina.ai/_images/jcloud-banner.png
:width: 0 %
:scale: 0 %
```

```{figure} img/jcloud-banner.png
:scale: 0 %
:width: 0 %
```

After building a Jina project, the next step is to deploy and host it on the cloud. [Jina AI Cloud](https://cloud.jina.ai/) is Jina's reliable, scalable and production-ready cloud-hosting solution that manages your project lifecycle without surprises or hidden development costs.

```{tip}
At present, Jina AI Cloud hosts all your Jina projects and offers computational/storage resources **for free**!
```

## Basics

Jina AI Cloud provides a CLI that you can use via `jina cloud` from the terminal (or `jcloud` or simply `jc` for minimalists.)

````{hint}
You can also install just the JCloud CLI without installing the Jina package.

```bash
pip install jcloud
jc -h
```

If you installed the JCloud CLI individually, all of its commands fall under the `jc` or `jcloud` executable.


In case the command `jc` is already occupied by another tool, use `jcloud` instead. If your pip install doesn't register bash commands for you, you can run `python -m jcloud -h`.
````

For the rest of this section, we use `jc` or `jcloud`. But again they are interchangable with `jina cloud`.

### Deploy

In Jina's idiom, a project is a [Flow](https://docs.jina.ai/fundamentals/flow/), which represents an end-to-end task such as indexing, searching or recommending. In this document, we use "project" and "Flow" interchangeably.

````{tip}
To deploy Flows on JCloud, all Executors need to be pushed to Jina Hub. If you haven't done so, please refer to [this guide](https://docs.jina.ai/chapters/hub/build-your-first-executor.html).
````


```{caution}
Flows have a maximum {ref}`lifetime<jcloud-lifetime>` after which they are automatically deleted.
```

A self-contained YAML file, consisting of all configuration at the [Flow](https://docs.jina.ai/fundamentals/flow/)-level and [Executor](https://docs.jina.ai/fundamentals/executor/)-level.

> All Executors' `uses` must follow the format `jinahub+docker://MyExecutor` (from [Executor Hub](https://cloud.jina.ai)) to avoid any local file dependencies:

```yaml
# flow.yml
jtype: Flow
executors:
  - name: sentencizer
    uses: jinahub+docker://Sentencizer
```

To deploy:

```bash
jc deploy flow.yml
```

````{tip}
We recommend testing locally before deployment:

```bash
jina flow --uses flow.yml
```
````

(jcloud-flow-status)=
### Get status

To get the status of a Flow:
```bash
jc status 15937a10bd
```

```{figure} img/status.png
:width: 70%
```

### Monitoring

Basic monitoring is provided to Flows deployed on Jina AI Cloud.

To access the [Grafana](https://grafana.com/)-powered dashboard, first get {ref}`the status of the Flow<jcloud-flow-status>`. The `dashboards` link is displayed at the bottom of the pane. Visit the URL to find basic metrics like 'Number of Request Gateway Received' and 'Time elapsed between receiving a request and sending back the response':

```{figure} monitoring.png
:width: 70%
```

### List Flows

To list all of your "ALIVE" Flows:

```bash
jc list
```

```{figure} img/list.png
:width: 70%
```

You can also filter your Flows by passing a phase:

```bash
jc list --phase Deleted
```


```{figure} img/list_deleted.png
:width: 70%
```

Or see all Flows:

```bash
jc list --status ALL
```

```{figure} img/list_all.png
:width: 70%
```

### Remove Flows

You can remove a single Flow, multiple Flows or even all Flows by passing different identifiers.

To remove a single Flow:

```bash
jc remove 173503c192
```

To remove multiple Flows:

```bash
jc remove 173503c192 887f6313e5 ddb8a2c4ef
```

To remove all Flows:

```bash
jc remove all
```

By default, removing multiple or all Flows is an interactive process where you must give confirmation before each Flow is deleted. To make it non-interactive, set the below environment variable before running the command:

```bash
export JCLOUD_NO_INTERACTIVE=1
```


## Restrictions

JCloud scales according to your needs. You can demand different resources (GPU/RAM/CPU/storage/instance-capacity) based on the needs of your Flows and Executors. If you have specific resource requirements, please contact us [on Slack](https://jina.ai/slack) or raise a [GitHub issue](https://github.com/jina-ai/jcloud/issues/new/choose).


```{admonition} Restrictions
  
- Deployments are only supported in the `us-east` region.
- Each Executor is allocated a maximum of 4GB RAM, 2 CPU cores & 10GB of block storage.
- Three Flows can be deployed at a time, out of which one Flow can use a GPU.
- A maximum of two GPUs are allocated per Flow.
- Flows with Executors using GPU are removed after 12 hours, whereas other Flows are removed after 72 hours.
```

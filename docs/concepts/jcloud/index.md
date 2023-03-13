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

In Jina's idiom, a project is a [Flow](https://docs.jina.ai/concepts/flow/), which represents an end-to-end task such as indexing, searching or recommending. In this document, we use "project" and "Flow" interchangeably.

```{caution}
Flows have a maximum lifetime after which they are automatically deleted.
```

A Flow can have two types of file structure: a single YAML file or a project folder.

#### Single YAML file

A self-contained YAML file, consisting of all configuration at the [Flow](https://docs.jina.ai/concepts/flow/)-level and [Executor](https://docs.jina.ai/concepts/executor/)-level.

> All Executors' `uses` must follow the format `jinaai+docker://<username>/MyExecutor` (from [Executor Hub](https://cloud.jina.ai)) to avoid any local file dependencies:

```yaml
# flow.yml
jtype: Flow
executors:
  - name: sentencizer
    uses: jinaai+docker://jina-ai/Sentencizer
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

#### Project folder

````{tip}
The best practice of creating a JCloud project is to use:

```bash
jc new
```
This ensures the correct project structure accepted by JCloud.

````

Just like a regular Python project, you can have sub-folders of Executor implementations and a `flow.yml` on the top-level to connect all Executors together.

You can create an example local project using `jc new hello`. The default structure looks like:

```
hello/
├── .env
├── executor1
│   ├── config.yml
│   ├── executor.py
│   └── requirements.txt
└── flow.yml
```

Where:

- `hello/` is your top-level project folder.
- `executor1` directory has all Executor related code/configuration. You can read the best practices for [file structures](https://docs.jina.ai/concepts/executor/executor-files/). Multiple Executor directories can be created.
- `flow.yml` Your Flow YAML.
- `.env` All environment variables used during deployment.

To deploy:

```bash
jc deploy hello
```

The Flow is successfully deployed when you see:

```{figure} img/deploy.png
:width: 70%
```
---

You will get a Flow ID, say `merry-magpie-82b9c0897f`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with the default gRPC gateway (feel free to change it to `http` or `websocket`), you can use `jina.Client` to access it:

```python
from jina import Client, Document

print(
    Client(host='grpcs://merry-magpie-82b9c0897f.wolf.jina.ai').post(
        on='/', inputs=Document(text='hello')
    )
)
```

(jcloud-flow-status)=
### Get status

To get the status of a Flow:
```bash
jc status merry-magpie-82b9c0897f
```

```{figure} img/status.png
:width: 70%
```

### Monitoring

Basic monitoring is provided to Flows deployed on Jina AI Cloud.

To access the [Grafana](https://grafana.com/)-powered dashboard, first get {ref}`the status of the Flow<jcloud-flow-status>`. The `Grafana Dashboard` link is displayed at the bottom of the pane. Visit the URL to find basic metrics like 'Number of Request Gateway Received' and 'Time elapsed between receiving a request and sending back the response':

```{figure} img/monitoring.png
:width: 80%
```

### List Flows

To list all of your "Serving" Flows:

```bash
jc list
```

```{figure} img/list.png
:width: 90%
```

You can also filter your Flows by passing a phase:

```bash
jc list --phase Deleted
```


```{figure} img/list_deleted.png
:width: 90%
```

Or see all Flows:

```bash
jc list --phase all
```

```{figure} img/list_all.png
:width: 90%
```

### Remove Flows

You can remove a single Flow, multiple Flows or even all Flows by passing different identifiers.

To remove a single Flow:

```bash
jc remove merry-magpie-82b9c0897f
```

To remove multiple Flows:

```bash
jc remove merry-magpie-82b9c0897f wondrous-kiwi-b02db6a066
```

To remove all Flows:

```bash
jc remove all
```

By default, removing multiple or all Flows is an interactive process where you must give confirmation before each Flow is deleted. To make it non-interactive, set the below environment variable before running the command:

```bash
export JCLOUD_NO_INTERACTIVE=1
```


### Update Flow

You can update a Flow by providing an updated YAML.

To update a Flow:

```bash
jc update super-mustang-c6cf06bc5b flow.yml
```

```{figure} img/update_flow.png
:width: 70%
```

### Pause / Resume Flow

You have the option to pause a Flow that is not currently in use but may be needed later. This will allow the Flow to be resumed later when it is needed again by using `resume`.

To pause a Flow:

```bash
jc pause super-mustang-c6cf06bc5b
```

```{figure} img/pause_flow.png
:width: 70%
```

To resume a Flow:

```bash
jc resume super-mustang-c6cf06bc5b
```

```{figure} img/resume_flow.png
:width: 70%
```

### Restart Flow, Executor or Gateway

If you need to restart a Flow, there are two options: restart all Executors and the Gateway associated with the Flow, or selectively restart only a specific Executor or the Gateway.

To restart a Flow:

```bash
jc restart super-mustang-c6cf06bc5b
```

```{figure} img/restart_flow.png
:width: 70%
```

To restart the Gateway:

```bash
jc restart super-mustang-c6cf06bc5b --gateway
```

```{figure} img/restart_gateway.png
:width: 70%
```

To restart an Executor:

```bash
jc restart super-mustang-c6cf06bc5b --executor executor0
```

```{figure} img/restart_executor.png
:width: 70%
```

### Scale an Executor
You can also manually scale any Executor.

```bash
jc scale good-martin-ca6bfdef84 --executor executor0 --replicas 2
```

```{figure} img/scale_executor.png
:width: 70%
```

## Restrictions

JCloud scales according to your needs. You can demand different resources (GPU/RAM/CPU/storage/instance-capacity) based on the needs of your Flows and Executors. If you have specific resource requirements, please contact us [on Slack](https://jina.ai/slack) or raise a [GitHub issue](https://github.com/jina-ai/jcloud/issues/new/choose).


```{admonition} Restrictions
  
- Deployments are only supported in the `us-east` region.
```

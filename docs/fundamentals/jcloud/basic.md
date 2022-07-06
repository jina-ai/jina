# Basic

```{tip}
JCloud client is an opensource project. [Check here for its repository](https://github.com/jina-ai/jcloud). 
```

## Install

```bash
pip install jcloud
jc -h
```

In case `jc` is already occupied by another tool, please use `jcloud` instead. If your pip install doesn't register bash commands for you, you can run `python -m jcloud -h`.


## Login

```bash
jc login
```

You can use a Google/GitHub account to register and login. Without logging in, you can't do anything.

## Deploy

In Jina's idiom, a project is a [Flow](https://docs.jina.ai/fundamentals/flow/), which represents an end-to-end task such as indexing, searching or recommending. In this README, we will use "project" and "Flow" interchangeably.

A Flow can have two types of file structure: a single YAML file or a project folder.

### A single YAML file

A self-contained YAML file, consisting of all configs at the [Flow](https://docs.jina.ai/fundamentals/flow/)-level and [Executor](https://docs.jina.ai/fundamentals/executor/)-level.

> All Executors' `uses` must follow the format `jinahub+docker://MyExecutor` (from [Jina Hub](https://hub.jina.ai)) to avoid any local file dependencies.

e.g.-

```yaml
# flow.yml
jtype: Flow
executors:
  - name: sentencizer
    uses: jinahub+docker://Sentencizer
```

To deploy,

```bash
jc deploy flow.yml
```

### A project folder

Just like a regular Python project, you can have sub-folders of Executor implementations; and a `flow.yml` on the top-level to connect all Executors together.

You can create an example local project using `jc new`. The default structure looks like:

```
.
├── .env
├── executor1
│   ├── config.yml
│   ├── executor.py
│   └── requirements.txt
└── flow.yml
```

where,

- `executor1` directory has all Executor related code/config. You can read the best practices for [file structures](https://docs.jina.ai/fundamentals/executor/executor-files/). Multiple such Executor directories can be created.
- `flow.yml` Your Flow YAML.
- `.env` All environment variables used during deployment.

To deploy,

```bash
jc deploy ./hello
```


The Flow is successfully deployed when you see:

```{figure} deploy.png
:width: 70%
```

You will get a Flow ID, say `173503c192`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with default gRPC gateway (feel free to change it to `http` or `websocket`), you can use `jina.Client` to access it:

```python
from jina import Client, Document

c = Client(host='https://173503c192.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```



## View logs

To watch the logs in realtime:

```bash
jc logs 173503c192
```

You can also stream logs for a particular Executor by passing its name:

```bash
jc logs 173503c192 --executor sentencizer
```

## Remove Flows

You can either remove a single Flow, multiple selected Flows or even all Flows by passing different kind of identifiers.

To remove a single Flow:

```bash
jc remove 173503c192
```

To remove multiple selected Flows:

```bash
jc remove 173503c192 887f6313e5 ddb8a2c4ef
```

To remove all Flows:

```bash
jc remove all
```

By default, removing multiple selected / all Flows would be in interactive mode where confirmation will be sent prior to
the deletion, to make it non-interactive to better suit your use case, set below environment variable before running the command:

```bash
export JCLOUD_NO_INTERACTIVE=1
```

## Get status

To get the status of a Flow:
```bash
jc status 15937a10bd
```

```{figure} status.png
:width: 70%
```

## Monitoring
To enable monitoring with the Flow, you can set `monitoring: true` in the Flow yaml and you'd be given access to a [Grafana](https://grafana.com/) dashboard.

To access the dashboard, get the status of the Flow first (see above section), at the bottom of the pane you should see the `dashboards` link. Visit the URL and you will find some basic metrics such as 'Number of Request Gateway Received' and 'Time elapsed between receiving a request and sending back the response':

```{figure} monitoring.png
:width: 70%
```

## List Flows

To list all the Flows you have:
```bash
jc list
```

You can see the ALIVE Flows deployed by you.

```{figure} list.png
:width: 70%
```


You can also filter your Flows by passing a status:

```bash
jc list --status FAILED
```


```{figure} list_failed.png
:width: 70%
```

Or see all the flows:

```bash
jc list --status ALL
```

```{figure} list_all.png
:width: 70%
```

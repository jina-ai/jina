# Advanced

## Environment variables

### A single YAML

```bash
jc deploy flow.yml --env-file flow.env
```


### A project folder

- You can include your environment variables in the `.env` file in the local project and JCloud will take care of managing them.
- You can optionally pass a `custom.env`.
  ```bash
  jc deploy ./hello --env-file ./hello/custom.env
  ```

## Fine-grained `resources` request

By default, `jcloud` allocates `100M` of RAM to each Executor. There might be cases where your Executor requires more memory. For example, DALLE-mini (generating image from text prompt) would need more than 100M to load the model. You can request higher memory for your Executor using `resources` arg while deploying the Flow (max 16G allowed per Executor).

```yaml
jtype: Flow
executors:
  - name: dalle_mini
    uses: jinahub+docker://DalleMini
    jcloud:
      resources:
        memory: 8G
```

## `spot` vs `on-demand` capacity

For cost optimization, `jcloud` tries to deploy all Executors on `spot` capacity. These are ideal for stateless Executors, which can withstand interruptions & restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g.- indexers) though.

```yaml
jtype: Flow
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
    jcloud:
      capacity: on-demand
```
(jcloud-external-executors)=
## Deploy external executors

You can also expose only the Executors by setting `expose_gateway` to `False`. Read more about {ref}`External Executors <external-executors>`

```yaml
jtype: Flow
jcloud:
  expose_gateway: false
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

```{figure} external-executor.png
:width: 70%
```


Similarly, you can also deploy & expose multiple External Executors.

```yaml
jtype: Flow
jcloud:
  expose_gateway: false
executors:
  - name: custom1
    uses: jinahub+docker://CustomExecutor1
  - name: custom2
    uses: jinahub+docker://CustomExecutor2
```

```{figure} external-executors-multiple.png
:width: 70%
```
## Deploy with specific `jina` version

To manage `jina` version while deploying a Flow to `jcloud`, you can pass `version` arg in the Flow yaml.

```yaml
jtype: Flow
jcloud:
  version: 3.4.11
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

## Flow retention days

In Jcloud, we have default life-cycle(24hrs) for each flow and we will remove flows periodically if they are beyond the life-cycle. To change the default behavior and manage it by yourself, you can setup `retention_days` args in `jcloud`. `-1` is never expired, `0` is to use the default life-cycle, or `X`(0<X<365), which means keep the flow utill X days. `0` is the default value if you don't pass `retention_days` argument.

```yaml
jtype: Flow
jcloud:
  retention_days: -1
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```
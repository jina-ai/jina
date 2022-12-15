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

## Deploy external executors

You can also expose the Executors only by setting `expose_gateway` to `false`. Read more about [External Executors.](https://docs.jina.ai/how-to/external-executor/)

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

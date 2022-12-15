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

## Request for fine-grained `resources`

### memory

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

### storage

We currently support 2 kinds of storage types [efs](https://aws.amazon.com/efs/) (default) and [ebs](https://aws.amazon.com/ebs/). The former one is a network file storage, whereas the latter is a block device.

````{note}

By default, we attach an `efs` to all the Executors in a Flow. The benefits of doing so are

- It can grow in size dynamically, so you don't need to shrink/grow volumes as & when necessary.
- All Executors in the Flow can share a disk.
- The same disk can also be shared with another Flow by passing a workspace-id while deploying a Flow.

```bash
jc deploy flow.yml --workspace-id <prev-flow-id>
```

If your Executor needs high IO, you can use `ebs` instead. Please note that,

- The disk cannot be shared with other Executors / Flows.
- You must pass a size of storage (default: `1G`, max `10G`).

````

```yaml
jtype: Flow
executors:
  - name: indexer1
    uses: jinahub+docker://SimpleIndexer
    jcloud:
      resources:
        storage:
          type: ebs
          size: 10G
  - name: indexer2
    uses: jinahub+docker://SimpleIndexer
    jcloud:
      resources:
        storage:
          type: efs
```

## Capacity (`spot` vs `on-demand`)

For cost optimization, `jcloud` tries to deploy all Executors on `spot` capacity. These are ideal for stateless Executors, which can withstand interruptions & restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g.- indexers) though.

```yaml
jtype: Flow
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
    jcloud:
      capacity: on-demand
```

## External executors

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

## `jina` version

To manage `jina` version while deploying a Flow to `jcloud`, you can pass `version` arg in the Flow yaml.

```yaml
jtype: Flow
jcloud:
  version: 3.4.11
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

(retention-days)=
## Retention days

In JCloud, we have a default life-cycle of 24hrs for Flows, after which they're removed, if idle. You can manage the same yourself by passing the right parameter for `retention-days` under `jcloud`. `0` is to use the default life-cycle, `X` (0<X<365), which is meant to keep the Flow alive until X days, and `-1` is for never expired,

```yaml
jtype: Flow
jcloud:
  retention_days: -1
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

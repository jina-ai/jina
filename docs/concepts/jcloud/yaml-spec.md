(jcloud-yaml-spec)=
# {octicon}`file-code` YAML specification

JCloud extends Jina's {ref}`Flow YAML specification<flow-yaml-spec>` by introducing the special field `jcloud`. This lets you define resources and scaling policies for each Executor and gateway.

Here's a Flow with two Executors that have specific resource needs. `indexer` demands 10G `ebs` disk, whereas `encoder` demands two cores, 8G RAM and two dedicated GPUs. 

```{code-block} yaml
---
emphasize-lines: 5-9,12-16
---
jtype: Flow
executors:
  - name: encoder
    uses: jinaai+docker://<username>/Encoder
    jcloud:
      resources:
        cpu: 2
        memory: 8G
        gpu: 1
  - name: indexer
    uses: jinaai+docker://<username>/Indexer
    jcloud:
      resources:
        storage: 
          type: ebs
          size: 10G
```

## Allocate Executor resources

Since each Executor has its own business logic, it may require different cloud resources. One Executor might need more RAM, whereas another might need a bigger disk. 

In JCloud, you can pass highly customizable, finely-grained resource requests for each Executor using the `jcloud.resources` argument in your Flow YAML.


### CPU

By default, `0.1 (1/10 of a core)` CPU is allocated to each Executor. You can use the `cpu` argument under `resources` to change it.

JCloud offers the general Intel Xeon processor (Skylake 8175M or Cascade Lake 8259CL) by default. 

```{hint}
Maximum of 16 cores is allowed per Executor.
```

```{code-block} yaml
---
emphasize-lines: 5-7
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        cpu: 0.5
```



### GPU

JCloud supports GPU workloads with two different usages: `shared` or `dedicated`. 

If GPU is enabled, JCloud will provide NVIDIA A10G Tensor Core GPUs with 24G memory for workloads in both usage types.

```{hint}
When using GPU resources, it may take a few extra minutes before all Executors are ready to serve traffic.
```

#### Shared GPU

An Executor using a `shared` GPU shares this GPU with up to four other Executors.
This enables time-slicing, which allows workloads that land on oversubscribed GPUs to interleave with one another.

```{code-block} yaml
---
emphasize-lines: 5-7
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        gpu: shared
```

```{caution}
The tradeoffs with a `shared` GPU are increased latency, jitter, and potential out-of-memory (OOM) conditions when many different applications are time-slicing on the GPU. If your application is memory consuming, we suggest using a dedicated GPU.
```

#### Dedicated GPU

Using a dedicated GPU is the default way to provision GPU for an Executor. This automatically creates nodes or assigns the Executor to land on a GPU node. In this case, the Executor owns the whole GPU. You can assign between 1 and 4 GPUs.

```{code-block} yaml
---
emphasize-lines: 5-7
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        gpu: 1
```

### Spot vs on-demand instance

For cost optimization, JCloud tries to deploy all Executors on `spot` capacity. This is ideal for stateless Executors, which can withstand interruptions and restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g. indexers) however.

```{code-block} yaml
---
emphasize-lines: 5-7
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        capacity: on-demand
```

### Memory

By default, `100M` of RAM is allocated to each Executor. You can use the `memory` argument under `resources` to change it.

```{hint}
Maximum of 16G RAM is allowed per Executor.
```

```{code-block} yaml
---
emphasize-lines: 5-7
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        memory: 8G
```


### Storage

JCloud supports three kinds of storage: ephemeral (default), [efs](https://aws.amazon.com/efs/) (network file storage) and [ebs](https://aws.amazon.com/ebs/) (block device).

`ephemeral` storage will assign space to an Executor when it is created. Data in `ephemeral` storage is deleted permanently if Executors are restarted or rescheduled.

````{hint}

By default, we assign `ephemeral` storage to all Executors in a Flow. This lets the storage resize dynamically, so you don't need to shrink/grow volumes manually.

If your Executor needs to share data with other Executors and retain data persistency, consider using `efs`. Note that:

- IO performance is slower compared to `ebs` or `ephemeral`
- The disk can be shared with other Executors or Flows.
- Default storage size is `5G`, maximum storage size parameter is `10G`.

If your Executor needs high IO, you can use `ebs` instead. Note that:

- The disk cannot be shared with other Executors or Flows.
- You must pass a storage size parameter (default: `1G`, max `10G`).

````
JCloud also supports retaining the data a Flow was using while active. You can set the `retain` argument to `true` to enable this feature.

```{code-block} yaml
---
emphasize-lines: 7-10,15-16
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      resources:
        storage:
          kind: ebs
          size: 10G
          retain: true
  - name: executor2
    uses: jinaai+docker://<username>/Executor2
    jcloud:
      resources:
        storage:
          kind: efs
```

## Scale out Executors

On JCloud, demand-based autoscaling functionality is naturally offered thanks to the underlying Kubernetes architecture. This means that you can maintain [serverless](https://en.wikipedia.org/wiki/Serverless_computing) deployments in a cost-effective way with no headache of setting the [right number of replicas](https://docs.jina.ai/how-to/scale-out/#scale-out-your-executor) anymore!


### Autoscaling with `jinaai+serverless://` 

The easiest way to scale out your Executor is to use a Serverless Executor. This can be enabled by using `jinaai+serverless://` instead of `jinaai+docker://` in Executor's `uses`, such as:

```{code-block} yaml
---
emphasize-lines: 4
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+serverless://<username>/Executor1
```

JCloud autoscaling leverages [Knative](https://knative.dev/docs/) behind the scenes, and `jinahub+serverless` uses a set of Knative configurations as defaults.

```{hint}
For more information about the Knative autoscaling configurations, please visit [Knative autoscaling](https://knative.dev/docs/serving/autoscaling/).
```


### Autoscaling with custom args

If `jinaai+serverless://` doesn't meet your requirements, you can further customize autoscaling configurations by using the `autoscale` argument on a per-Executor basis in the Flow YAML, such as:

```{code-block} yaml
---
emphasize-lines: 5-10
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      autoscale:
        min: 1
        max: 2
        metric: rps
        target: 50
```

Below are the defaults and requirements for the configurations:

| Name   | Default     | Allowed                  | Description                                       |
| ------ | ----------- | ------------------------ | ------------------------------------------------- |
| min    | 1           | int                      | Minimum number of replicas (`0` means serverless) |
| max    | 2           | int, up to 5             | Maximum number of replicas                        |
| metric | concurrency | `concurrency`  /   `rps` | Metric for scaling                                |
| target | 100         | int                      | Target number after which replicas autoscale      |

After JCloud deployment using the autoscaling configuration, the Flow serving part is just the same: the only difference you may notice is it takes a few extra seconds to handle the initial requests since it needs to scale the deployments behind the scenes. Let JCloud handle the scaling from now on, and you can deal with the code!

## Configure availability tolerance

If service issues cause disruption of Executors, JCloud lets you specify a tolerance level for number of replicas that stay up or go down.

The JCloud parameters `minAvailable` and `maxUnavailable` ensure that Executors will stay up even if a certain number of replicas go down.

| Name             | Default |                                          Allowed                                          | Description                                              |
|:-----------------|:-------:|:-----------------------------------------------------------------------------------------:|:---------------------------------------------------------|
 | `minAvailable`   |   N/A   | Lower than number of [replicas](https://docs.jina.ai/concepts/flow/scale-out/#scale-out)  | Minimum number of replicas available during disruption   |
| `maxUnavailable` |   N/A   | Lower than numbers of [replicas](https://docs.jina.ai/concepts/flow/scale-out/#scale-out) | Maximum number of replicas unavailable during disruption |

```{code-block} yaml
---
emphasize-lines: 5-6
---
jtype: Flow
executors:
  - uses: jinaai+docker://<username>/Executor1
    replicas: 5
    jcloud:
      minAvailable: 2
```
> In case of disruption, ensure at least two replicas will still be available, while three may be down.

```{code-block} yaml
---
emphasize-lines: 5-6
---
jtype: Flow
executors:
  - uses: jinaai+docker://<username>/Executor1
    replicas: 5
    jcloud:
      maxUnavailable: 2
```
> In case of disruption, ensure that if a maximum of two replicas are down, at least three replicas will still be available.


## Configure Gateway

JCloud provides support Ingress gateways to expose your Flows to the public internet with TLS.

In JCloud. We use [Let's Encrypt](https://letsencrypt.org/) for TLS.

```{hint}
The JCloud gateway is different from Jina's gateway. In JCloud, a gateway works as a proxy to distribute internet traffic between Flows, each of which has a Jina gateway (which is responsible for managing external gRPC/HTTP/WebSocket traffic to your Executors)
```

### Set timeout

By default, the JCloud gateway will close connections that have been idle for over 600 seconds. If you want a longer connection timeout threshold, change the `timeout` parameter under `gateway.jcloud`.

```{code-block} yaml
---
emphasize-lines: 2-4
---
jtype: Flow
gateway:
  jcloud:
    timeout: 600
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
```

### Control gateway resources

To customize the gateway's CPU or memory, specify the `memory` and/or `cpu` arguments under `gateway.jcloud.resources`:

```{code-block} yaml
---
emphasize-lines: 2-6
---
jtype: Flow
gateway:
  jcloud:
    resources:
      memory: 800M
      cpu: 0.4
executors:
  - name: encoder
    uses: jinaai+docker://<username>/Encoder
```

## Expose Executors

A Flow deployment without a Gateway is often used for {ref}`external-executors`, which can be shared between different Flows. You can expose an Executor by setting `expose: true` (and un-expose the Gateway by setting `expose: false`):

```{code-block} yaml
---
emphasize-lines: 2-4, 8-9
---
jtype: Flow
gateway:
  jcloud:
    expose: false       # don't expose the Gateway
executors:
  - name: custom
    uses: jinaai+docker://<username>/CustomExecutor
    jcloud:
      expose: true    # expose the Executor
```

```{figure} img/expose-executor.png
:width: 70%
```

You can expose the Gateway along with Executors:

```{code-block} yaml
---
emphasize-lines: 2-4,8-9
---
jtype: Flow
gateway:
  jcloud:
    expose: true
executors:
  - name: custom1
    uses: jinaai+docker://<username>/CustomExecutor1
    jcloud:
      expose: true    # expose the Executor
```

```{figure} img/gateway-and-executors.png
:width: 70%
```

## Other deployment options

### Specify Jina version

To control Jina's version while deploying a Flow to `jcloud`, you can pass the `version` argument in the Flow YAML:

```{code-block} yaml
---
emphasize-lines: 2-3
---
jtype: Flow
jcloud:
  version: 3.10.0
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
```

### Add Labels

You can use `labels` (as key-value pairs) to attach metadata to your Flows and Executors:

Flow level `labels`:
```{code-block} yaml
---
emphasize-lines: 2-5
---
jtype: Flow
jcloud:
  labels: 
    username: johndoe
    app: fashion-search
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
```

Executor level `labels`:
```{code-block} yaml
---
emphasize-lines: 5-8
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      labels:
        index: partial
        group: backend
```


```{hint}

Keys in `labels` have the following restrictions:
  - Must be 63 characters or fewer.
  - Must begin and end with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and alphanumerics between.
  - The following keys are skipped if passed in the Flow YAML.
    - `user`
    - `jina`-version
```

### Monitoring

To enable [tracing support](https://docs.jina.ai/cloud-nativeness/opentelemetry/) in Flows, you can pass `enable: true` argument in the Flow YAML. (Tracing support is not enabled by default in JCloud)

```{code-block} yaml
---
emphasize-lines: 2-5
---
jtype: Flow
jcloud:
  monitor:
    traces:
      enable: true
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
```

You can pass the `enable: true` argument to `gateway`, so as to only enable the tracing support in gateway:

```{code-block} yaml
---
emphasize-lines: 2-5
---
jtype: Flow
gateway:
  jcloud:
      monitor:
        traces:
          enable: true
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
```

You can also only enable tracing support in `executor1`.

```{code-block} yaml
---
emphasize-lines: 5-8
---
jtype: Flow
executors:
  - name: executor1
    uses: jinaai+docker://<username>/Executor1
    jcloud:
      monitor:
        traces:
          enable: true
```

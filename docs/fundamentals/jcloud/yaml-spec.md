(jcloud-yaml-spec)=
# {octicon}`file-code` YAML specification

Built on top of {ref}`Flow YAML specification<flow-yaml-spec>`, JCloud YAML extends it by introducing a special field `jcloud`. With it, one can define resources and scaling policies for each Executor and Gateway.

Here's a Flow with 2 Executors with specific resource needs. `indexer` demands for 10G `ebs` disk, whereas `encoder` demands for 2 cores, 8G RAM & 2 dedicated GPUs. 

```{code-block} yaml
---
emphasize-lines: 5-9,12-16
---
jtype: Flow
executors:
  - name: indexer
    uses: jinahub+docker://Indexer
    jcloud:
      resources:
        storage: 
          type: ebs
          size: 10G
  - name: encoder
    uses: jinahub+docker://Encoder
    jcloud:
      resources:
        cpu: 2
        memory: 8G
        gpu: 2
```

## Allocate resources for Executors

Since each Executor has its own business logic, it might require different Cloud resources. One might need a higher RAM, whereas another might need a bigger disk. 

In JCloud, we allow users to pass highly customizable, fine-grained resource requests for each Executor using `jcloud.resources` argument in your Flow YAML.


### CPU

By default, `0.1 (1/10 of a core)` CPU is allocated to each Executor. You can use `cpu` arg under `resources` to customise it.

JCloud offers the general Intel Xeon processor (Skylake 8175M or Cascade Lake 8259CL) by default. 

```{hint}
Maximum of 16 cores is allowed per Executor.
```

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
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

An executor using a `shared` GPU shares this GPU with up to 4 other Executors.
This enables a time-slicing, which allows workloads that land on oversubscribed GPUs to interleave with one another.

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      resources:
        gpu: shared
```

```{caution}
The tradeoffs with `shared` GPU are increased latency, jitter, and potential out-of-memory (OOM) conditions when many different applications are time-slicing on the GPU. If your application is memory consuming, we suggest using a dedicated GPU.
```

#### Dedicated GPU

Using a dedicated GPU is the default way to provision GPU for the Executor. This will automatically create nodes or assign the Executor to land on a GPU node. In this case, executor owns the whole GPU. You can assign between 1 and 4 GPUs.

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      resources:
        gpu: 2
```

### Spot vs on-demand instance

For cost optimization, `jcloud` tries to deploy all Executors on `spot` capacity. These are ideal for stateless Executors, which can withstand interruptions & restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g.- indexers) though.

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      capacity: on-demand
```

### Memory

By default, `100M` of RAM is allocated to each Executor. You can use `memory` arg under `resources` to customise it.

```{hint}
Maximum of 16G RAM is allowed per Executor.
```

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      resources:
        memory: 8G
```


### Storage

JCloud supports 2 kinds of Storage types [efs](https://aws.amazon.com/efs/) (default) and [ebs](https://aws.amazon.com/ebs/). The former one is a network file storage, whereas the latter is a block device.

````{hint}

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
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      resources:
        storage:
          type: ebs
          size: 10G
  - name: executor2
    uses: jinahub+docker://Executor2
    jcloud:
      resources:
        storage:
          type: efs
```

## Scale out Executors

On JCloud, demand-based autoscaling functionality is naturally offered thanks to the underlying Kubernetes architecture. This means that you can maintain [serverless](https://en.wikipedia.org/wiki/Serverless_computing) deployments in a cost-effective way with no headache of setting the [right number of replicas](https://docs.jina.ai/how-to/scale-out/#scale-out-your-executor) anymore!


### Autoscaling with `jinahub+serveless://` 

The easiest way to scale out your Executor is to use Serverless Executor. This can be enabled by simply use `jinahub+serverless://` instead of `jinahub+docker://` in Executor's `uses`, such as:

```{code-block} yaml
---
emphasize-lines: 4
---
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+serverless://Executor1
```

JCloud autoscaling leverages [Knative](https://knative.dev/docs/) behind the scenes, and `jinahub+serverless` uses a set of Knative configurations as defaults.

```{hint}
For more information about the Knative Autoscaling configurations, please visit [Knative Autoscaling](https://knative.dev/docs/serving/autoscaling/).
```


### Scale-out manually

If `jinahub+serverless://` doesn't meet your requirements, you can further customize Autoscaling configurations by using the `autoscale` argument on a per-Executor basis in the Flow YAML, such as:

```{code-block} yaml
---
emphasize-lines: 5-10
---
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      autoscale:
        min: 1
        max: 2
        metric: rps
        target: 50
```

Below are the defaults and requirements for the configurations:

| Name   | Default     | Allowed                  | Description                                     |
| ------ | ----------- | ------------------------ | ----------------------------------------------- |
| min    | 1           | int                      | Minimum number of replicas (0 means serverless) |
| max    | 2           | int, up to 5             | Maximum number of replicas                      |
| metric | concurrency | `concurrency`  /   `rps` | Metric for scaling                              |
| target | 100         | int                      | Target number after which replicas autoscale    |

After JCloud deployment using the Autoscaling configurations, the Flow serving part is just the same; the only difference you would probably notice is it may take extra seconds
to handle the initial requests since it may need to scale the deployments behind the scenes. Let JCloud handle the scaling from now on, and you should only worry about the code!


## Config Gateway

To expose users' Flows to the public Internet with TLS, JCloud provides support Ingress Gateways.

In JCloud. We use [Let's Encrypt](https://letsencrypt.org/) for TLS.

```{hint}
The JCloud gateway is different from Jina's Gateway. In JCloud, a gateway works as a proxy to distribute internet traffic between Flows, each of which has a Jina Gateway (which is responsible for managing external gRPC/HTTP/Websocket traffic to your Executors)
```

### Set timeout

By default, JCloud gateway will close connections that have been idle for over `600` seconds. If you want longer connection timeout threshold, you can consider changing the `timeout` parameter in `gateway`.

```yaml
jtype: Flow
jcloud:
  gateway:
    timeout: 600
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

### Control resources of the Gateway

If you'd like to customize the Gateway's CPU or memory, `memory` / `cpu` arg needs to be specified under `jcloud.gateway.resources` as follows:

```{code-block} yaml
---
emphasize-lines: 3-7
---
jtype: Flow
jcloud:
  gateway:
    resources:
      memory: 800M
      cpu: 0.4
executors:
  - name: encoder
    uses: jinahub+docker://Encoder
```

### Disable Gateway

A Flow deployment without a Gateway is often used as {ref}`external-executors`, which can be shared over different Flows. One can disable Gateway by setting `expose_gateway: false`:

```{code-block} yaml
---
emphasize-lines: 3
---
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

You can also deploy & expose multiple External Executors.

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

## Other deployment options

### Specify Jina version

To control Jina's version while deploying a Flow to `jcloud`, you can pass `version` arg in the Flow yaml.

```yaml
jtype: Flow
jcloud:
  version: 3.4.11
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

### Add Labels

You can use `labels` (as key-value pairs) to attach metadata to your Flows.

```yaml
jtype: Flow
jcloud:
  labels: 
    username: johndoe
    app: fashion-search
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

```{hint}

Keys in `labels` have the following restrictions.
  - Must be 63 characters or less.
  - Must begin and end with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and alphanumerics between.
  - Following keys are skipped if passed in the Flow YAML.
    - user
    - jina-version
    - retention-days
```

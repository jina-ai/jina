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

### GPU support

We have GPU support in JCloud. We have two kind of GPU usages, `shared` and `dedicated`.

```{note}
When using GPU resources, it may take an extra 2-3 mins until all Flows are running in the cluster.
This is because enabling GPU support may require the cluster to dynamically provision new GPU nodes.
```

#### Shared GPU

An executor using a `shared` GPU shares this GPU with up to 10 other users.
This enables a time-slicing feature, which allows workloads that land on oversubscribed GPUs to interleave with one another.

To enable a shared GPU resource, specify it in your YAML configuration:

```yaml
jtype: Flow
protocol: http
executors:
- name: sb0
  uses: jinahub+docker://CustomExecutor
  jcloud:
      resources:
        gpu: shared
```

```{caution}
There are no special previsions in place to isolate replicas that run on the same underlying GPU. Each workload has access to the GPU memory and runs in the same fault-domain as of all the others. Therefore, if one workload crashes, they all do. 
```

#### Dedicated GPU

Using a dedicated GPU is a default way to provision GPU to the Executor. This will automatically create nodes or assign the Executor to land on a GPU node. In this case, executor owns the whole GPU. You can assign between 1 and 4 GPUs.

To enable a shared GPU resource, specify it in your YAML configuration:

```yaml
jtype: Flow
protocol: http
executors:
- name: sb0
  uses: jinahub+docker://CustomExecutor
  jcloud:
      resources:
        gpu: 2
```

### Gateway

For internet exposure, JCloud now provides support for [Kong gateway](https://konghq.com/products/api-gateway-platform). 

```{note}
The JCloud gateway is a different concept from Jina gateway. In JCloud, a gateway service is working as a proxy to distribute internet traffic between Flows, each of which has a Jina gateway. Jina gateways are there to manage external https/grpcs/websockets protocol service to Flows.
```

We currently support two types of gateway for internet exposure: [Kong gateway](https://konghq.com/products/api-gateway-platform) and [Application Load Balancer (ALB)](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html).

#### ALB

At the current stage, ALB is the default gateway type due to backward compatibility. ALB has the features listed [here] (https://aws.amazon.com/elasticloadbalancing/application-load-balancer/).
For the purposes of Jina, the following features are most important:

- Use AWS signed public certs

#### Kong Gateway

Kong Gateway is the recommended gateway in JCloud.
Kong is currently working as ingress controller, and we will enable other [Kong features](https://docs.konghq.com/kubernetes-ingress-controller/latest/) in the future.
For the purposes of Jina, the following features are most important:

- Use Let's Encrypt signed wildcard certificates
- Use NGINX to distribute traffic as ingress controller

```{tip}
Normally, user can retrieve the CA (certificate authority) from client end. The difference of cert CA usually will not affect the jina usage unless the CA is not in the trust list.
```

```{admonition} Why Kong? 
Since we are using EKS as JCloud's Kubernetes cluster, ALB can be used to provide a simple loadbalancing service to our executor. However, there are some drawbacks:
1). ALB is not a general Kubernetes services. Instead, it is provided by AWS, which means that we can't use it with other cloud provider.
2). ALB is simple to configure and use, but it doesn't have features like horizontal scaling, route methods configuration, etc.
3). ALB is layer 7 loadbalancer and Kong is using a layer 4 loadbalancer and route traffic via Kong Ingress Controller. Therefore, Kong is able to support tcp/udp protocols, whereas ALB can only support grpc/https/http.

JCloud is currenlty in progress of migrating from ALB to Kong, and we recommend the usage of `kong` as gateway. However, `alb` is currently still supported for backward compatibility.
```

### Usage

To enable Kong Gateway instead of ALB, specify the gateway type as `kong` in your JCloud YAML:

```yaml
jtype: Flow
jcloud:
    gateway:
        type: kong
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
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

In JCloud, we have a default life-cycle of 24hrs for Flows, after which they're removed if idle. You can manage the same yourself by passing the right parameter for `retention-days` under `jcloud`. `0` is to use the default life-cycle, `X` (0<X<365), which is meant to keep the Flow alive until X days, and `-1` is for never expired,

```yaml
jtype: Flow
jcloud:
  retention_days: -1
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

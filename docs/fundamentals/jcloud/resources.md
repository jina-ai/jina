## Resources

Since each Executor has its own business logic, it might need different Cloud resources. One might need a higher RAM, whereas another might need a bigger disk. 

In JCloud, we allow users to pass highly customizable, fine-grained resource requests for each Executor using `resources` argument in your Flow YAML.

#### Memory

By default, `100M` of RAM is allocated to each Executor. You can use `memory` arg under `resources` to customise it.

```{note}
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

#### CPU

By default, `0.1 (1/10 of a core)` CPU is allocated to each Executor. You can use `cpu` arg under `resources` to customise it.

JCloud offers the general Intel Xeon processor (Skylake 8175M or Cascade Lake 8259CL) by default. 

```{note}
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

#### Storage

JCloud supports 2 kinds of Storage types [efs](https://aws.amazon.com/efs/) (default) and [ebs](https://aws.amazon.com/ebs/). The former one is a network file storage, whereas the latter is a block device.

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

#### GPU

JCloud supports GPU workloads with two different usages: `shared` or `dedicated`. 

If GPU is enabled, JCloud will provide NVIDIA A10G Tensor Core GPUs for workloads in both usage types.

```{note}
When using GPU resources, it may take few extra mins until all Executors ready to serve traffic.
```

##### Shared

An executor using a `shared` GPU shares this GPU with up to 10 other Executors.
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
There are no special provisions in place to isolate replicas that run on the same underlying GPU. Each workload has access to the GPU memory and runs in the same fault-domain as of all the others. Therefore, if one workload crashes, they all do. 
```

##### Dedicated

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


### Example

Here's a Flow with 2 Executors with specific resource needs. `indexer` demands for 10G `ebs` disk, whereas `encoder` demands for 2 cores, 8G RAM & 2 dedicated GPUs. 

```yaml
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

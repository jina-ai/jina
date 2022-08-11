# Autoscaling

In JCloud, demand-based autoscaling functionality is naturally offered thanks to the underlying Kubernetes architecture. This means that you can maintain [serverless](https://en.wikipedia.org/wiki/Serverless_computing) deployments in a cost-effective way with no headache of setting the [right number of replicas](https://docs.jina.ai/how-to/scale-out/#scale-out-your-executor) anymore!

## Configurations
Autoscaling configurations can be specified on a per Executor basis using the `autoscale` argument in your Flow YAML, such as:

```yaml
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

Below are the configurations explained in detail:

```{note}
JCloud Autoscaling leverages [Knative](https://knative.dev/docs/), where the configurations are directly supported. For more information, please visit [Knative Autoscaling](https://knative.dev/docs/serving/autoscaling/).
```


| Name   | Default     | Allowed                   | Description                                                      |
|--------|-------------|---------------------------|------------------------------------------------------------------|
| min    | 1           | int                       | Minimum number of replicas (0 means serverless)                  |
| max    | 2           | int                       | Maximum number of replicas (up to 5)                             |
| metric | concurrency | `concurrency`   /   `rps` | Metric for scaling                                               |
| target | 100         | int                       | Target number for concurrency/rps after which replicas autoscale |

## Serverless

We also support using `jinahub+serverless` protocol for Exectuor's `uses` in the Flow YAML to indiciate the enrollment of Autoscaling, such as:

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+serverless://Executor1
```

Example above will take the following defaults:

| min | max | metric      | target |
|-----|-----|-------------|--------|
| 0   | 2   | concurrency | 100    |

After JCloud deployment using the Autoscaling configurations, the Flow serving part is just the same; the only difference you would probably notice is it may take extra seconds
to handle the initial requests since it may need to scale the deployments behind the scenes. Let JCloud handle the scaling from now on and you should only worry about the code!

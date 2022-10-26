# Autoscaling

In JCloud, demand-based autoscaling functionality is naturally offered thanks to the underlying Kubernetes architecture. This means that you can maintain [serverless](https://en.wikipedia.org/wiki/Serverless_computing) deployments in a cost-effective way with no headache of setting the [right number of replicas](https://docs.jina.ai/how-to/scale-out/#scale-out-your-executor) anymore!

## Serverless

Autoscaling can be enabled by using `jinahub+serverless` protocol for Exectuor's `uses` in the Flow YAML, such as:

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+serverless://Executor1
```

JCloud Autoscaling leverages [Knative](https://knative.dev/docs/) behind the scenes, and `jinahub+serverless` uses a set of Knative configuratons as defaults:

```{note}
For more information about the Knative Autoscaling configurations, please visit [Knative Autoscaling](https://knative.dev/docs/serving/autoscaling/).
```

| Name   | Value       | Description                                     |
|--------|-------------|-------------------------------------------------|
| min    | 0           | Minimum number of replicas (0 means serverless) |
| max    | 2           | Maximum number of replicas                      |
| metric | concurrency | Metric for scaling                              |
| target | 100         | Target number after which replicas autoscale    |

## Configurations

If `jinahub+serverless` doesn't meet your requirements, you can further customize Autoscaling configurations by using the `autoscale` argument on a per Executor basis in the Flow YAML, such as:

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

Below are the defaults and requirements for the configurations:

| Name   | Default     | Allowed                  |
|--------|-------------|--------------------------|
| min    | 1           | int                      |
| max    | 2           | int, up to 5             |
| metric | concurrency | `concurrency`  /   `rps` |
| target | 100         | int                      |

After JCloud deployment using the Autoscaling configurations, the Flow serving part is just the same; the only difference you would probably notice is it may take extra seconds
to handle the initial requests since it may need to scale the deployments behind the scenes. Let JCloud handle the scaling from now on and you should only worry about the code!

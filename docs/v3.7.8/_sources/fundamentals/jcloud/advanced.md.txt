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

## jina version

To manage `jina` version while deploying a Flow to `jcloud`, you can pass `version` arg in the Flow yaml.

```yaml
jtype: Flow
jcloud:
  version: 3.4.11
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

## Capacity (`spot` vs `on-demand`)

For cost optimization, `jcloud` tries to deploy all Executors on `spot` capacity. These are ideal for stateless Executors, which can withstand interruptions & restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g.- indexers) though.

```yaml
jtype: Flow
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
    jcloud:
      capacity: on-demand
```

(external-executors)=
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

## Internet Exposure & TLS

To expose users' Flows to the internet with TLS, JCloud provides support for 2 Gateways [ALB](https://aws.amazon.com/elasticloadbalancing/application-load-balancer/) & [Kong API Gateway](https://konghq.com/products/api-gateway-platform). 

```{note}
The JCloud gateway is different from Jina's Gateway. In JCloud, a gateway works as a proxy to distribute internet traffic between Flows, each of which has a Jina Gateway (which is responsible to manage external gRPC/HTTP/Websocket traffic to your Executors)
```

### ALB

Currently ALB is the default gateway for backward compatibility. We use AWS provided public certificates for TLS with the ALB.

### Kong

Kong is the recommended gateway in JCloud. We use [Let's Encrypt](https://letsencrypt.org/) for TLS with Kong. To enable Kong Gateway instead of ALB, specify the gateway ingress kind as `kong` in your JCloud YAML:

```yaml
jtype: Flow
jcloud:
  gateway:
    ingress: kong
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

(retention-days)=
## Retention days

In JCloud, we have a default life-cycle of 24hrs for Flows, after which they're removed if idle. You can manage the same yourself by passing the right parameter for `retention-days` under `jcloud`. `0` is to use the default life-cycle, `X` (0<X<365), which is meant to keep the Flow alive until X days, and `-1` is for never expired,

```yaml
jtype: Flow
jcloud:
  retention_days: -1
executors:
  - name: executor1
    uses: jinahub+docker://Executor1
```

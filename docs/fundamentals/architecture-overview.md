# Architecture Overview

This figure shows an overview of how Jina deploys and serves its Flows and Executors.

This figure shows details on how `Flow` and `Executor` abstractions translate into concrete entities to provide all the 
serving and scaling features of Jina.

This architecture is useful to understand how Jina works regardless of it working locally orchestrated by the Flow or in 
a cloud-native infrastructure as Kubernetes. In fact, you can notice how the naming and concepts are inspired by Kubernetes architecture.
 

```{figure} arch-overview.svg
:align: center
```

- **Flow**: The {ref}`Flow <flow>` ties Executors together into a processing pipeline.

- **Executor**: {ref}`Executor <executor>` performs tasks on DocumentArrays.

- **Gateway**: Gateway is a service started by the Flow which is responsible for exposing the `HTTP`, `WebSocker` or `gRPC` endpoints to the client, and
keeps knowledge of the topology of the Flow to guarantee that the `docs` are processed by the Executors in the proper order. It communicates with the Deployments via `gRPC`

- **Deployment**: Deployment is an abstraction around Executor that lets the `Gateway` communicate with an Executor abstracting their internal replication details.

- **Pod**: A Pod is a simple abstraction over a runtime running any of Jina service, let it be a process, a docker container or a Kubernetes Pod.

- **Head**: Head is a service added by Jina inside a Deployment to make sure that load is balanced between all replicas of Executors. It communicates with the Executors via `gRPC`

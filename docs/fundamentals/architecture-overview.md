# Architecture Overview

This figure shows an overview of how Jina deploys and serves its Flows and Executors.

This figure shows details on how `Flow` and `Executor` abstractions translate into concrete entities, providing all the 
serving and scaling features of Jina.

You will not need to understand every detail of this architecture in order to build your first Neural Search app using Jina. But it is useful in order to understand how Jina works, regardless of whether it runs locally, orchestrated only by the Flow, or if it runs in 
a cloud-native infrastructure such as Kubernetes. In fact, you can notice how some of the naming and concepts are inspired by the Kubernetes architecture.
 

```{figure} arch-overview.svg
:align: center
```

- **Flow**: The {ref}`Flow <flow>` ties Executors together into a processing pipeline.

- **Executor**: Each {ref}`Executor <executor>` performs a single task on `DocumentArray`s.

- **Gateway**: The Gateway is a service started by the Flow which is responsible for exposing the `HTTP`, `WebSocker` or `gRPC` endpoints to the client. Additionally, it
keeps knowledge of the topology of the Flow to guarantee that the `Documents` are processed by the Executors in the proper order. It communicates with the Deployments via `gRPC`

- **Deployment**: Deployment is an abstraction around Executor that lets the `Gateway` communicate with an Executor. It encapsulates and abstracts internal replication details.

- **Pod**: A Pod is a simple abstraction over a runtime that runs any Jina service, be it a process, a Docker container, or a Kubernetes Pod.

- **Head**: The Head is a service added to a Deployment by Jina, and it ensures that load is balanced between all replicas of a given Executor. It communicates with the Executors via `gRPC`.

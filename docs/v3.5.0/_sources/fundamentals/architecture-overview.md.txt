(architecture-overview)=
# Architecture Overview

The figure below shows details on how the Flow and Executor abstractions translate into concrete microservices, providing all the 
serving and scaling features of Jina.


```{figure} arch-overview.svg
:align: center
```

You will not need to understand every detail of this architecture in order to build your first Neural Search app using Jina.
But it is useful in order to understand how Jina works, regardless of whether your microservice app runs locally,
is orchestrated only by the Flow object itself, or is deployed using a cloud-native infrastructure such as Kubernetes.
In fact, you might notice how some naming and concepts are inspired by the Kubernetes architecture.

The following concepts may appear in the docs, but you don't need to master them as they are mainly designed for advanced or internal use:

  - **Gateway**: The Gateway is a service started by the Flow which is responsible for exposing the `HTTP`, `Websocket` or `gRPC` endpoints to the client. It is the service that the clients of your app will actually talk to. Additionally, it keeps knowledge of the topology of the Flow to guarantee that the `Documents` are processed by the Executors in the proper order. It communicates with the Deployments via `gRPC`.

  - **Deployment**: Deployment is an abstraction around Executor that lets the `Gateway` communicate with an Executor. It encapsulates and abstracts internal replication details.

  - **Pod**: A Pod is a simple abstraction over a runtime that runs any Jina service, be it a process, a Docker container, or a Kubernetes Pod.

  - **Head**: The Head is a service added to a sharded Deployment by Jina. It manages the communication to the different shards based on the configured polling strategy. It communicates with the Executors via `gRPC`.

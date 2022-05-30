# When things go wrong

## Exceptions in Executor code

## Exception in Executor or Head runtime

## Executor or Head cannot be reached

When an {ref}`Executor or Head <architecture-overview>` can't be reached by the Flow's gateway, it attempts to re-connect
to the faulty deployment according to a retry policy.
The specifics of this policy depend on the environment the Flow find itself in, and are lined out below.

If, during the complete execution of this policy, no successful call to any Executor replica could be made, the request is aborted
and the failure is {ref}`reported to the client <failure-reporting>`).

### Request retry policy: Local deployment

If a Flow is deployed locally (with or without {ref}`containerized Executors <dockerize-exec>`), the following policy
for failed requests applies on a per-Executor basis:

- If there are multiple replicas of the given Executor, try each replica at least once, or until it succeeds
- Irrespective of the number of replicas, try the request at least 3 times, or until it succeeds. If there are fewer than 3 replicas, try them in a round-robin fashion

### Request retry policy: Deployment with Kubernetes

If a Flow is {ref}`deployed in Kubernetes <kubernetes>`, retries cannot be distributed to different replicas of the same Executor.

````{admonition} See Also
:class: seealso

The impossibility of retries across different replicas is a limitation of Kubernetes in combination with gRPC.
If you want to learn more about this limitation, see [this](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/) Kubernetes Blog post.

An easy way to overcome this limitation is to use a service mesh like [Linkerd](https://linkerd.io/).
````

Concretely, this results in the following per-Executor retry policy:

- Try the request 3 times, or until it succeeds, always on the same replica of the Executor

### Request retry policy: Deployment with Kubernetes and a service mesh

A Kubernetes service mesh can enable load balancing, and thus retries, between replicas of an Executor.

````{admonition} Hint
:class: hint
While Jina supports any service mesh, the output `f.to_k8s_yaml()` already includes the necessary annotation for Linkerd.
````

If a service mesh is installed alongside Jina in the Kubernetes cluster, the following retry policy applies for each Executor:

- Try the request at least 3 times, or until it succeeds
- Distribute the requests to the replicas according to the service mesh's configuration


````{admonition} Caution
:class: caution

Many service meshes have the ability to perform retries themselves.
Be careful about setting up service mesh level retries in combination with Jina, as it may lead to unwanted behaviour in combination with
Jina's own retry policy.
````

(failure-reporting)=
### Failure reporting

If the retry policy is exhausted for a given request, the error is reposted back to the corresponding client.

The resulting error message will contain the *network address* of the failing Executor.
If multiple replicas are present, all addresses will be reported - unless the Flow is deployed using Kubernetes, in which
case the replicas are managed by k8s and only a single address is available.

Depending on the client-to-gateway protocol, the error message will be returned in the following ways:

- **gRPC**: A response with the gRPC status code 14 (*UNAVAILABLE*) is issued, and the error message is contained in the `details` field
- **HTTP**: A response with the HTTP status code 503 (*SERVICE_UNAVAILABLE*) is issues, and the error message is contained in `response['header']['status']['description']`
- **WebSocket**: The stream closes with close code 1011 (*INTERNAL_ERROR*) and the message is contained in the WS close message

For any of these protocols, the {ref}`Jina Client <client>` will raise a `ConnectionError` containing the error message.
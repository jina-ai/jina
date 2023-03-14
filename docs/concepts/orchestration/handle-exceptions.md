(flow-error-handling)=
# Handle Exceptions

When building a complex solution, things sometimes go wrong. Jina does its best to recover from failures, handle them gracefully, and report useful failure information to the user.

The following outlines (more or less) common failure cases, and explains how Jina responds to each.

## Executor errors

In general there are two places where an Executor level error can happen:

- If an {class}`~jina.Executor`'s `__init__` method raises an Exception, the {class}`~jina.Flow` cannot start. In this case this Executor runtime raises the Exception, and the Flow throws a `RuntimeFailToStart` Exception.
- If one of the Executor's `@requests` methods raises an Exception, the error message is added to the response and sent back to the client. If the gRPC or WebSockets protocols are used, the networking stream is not interrupted and can accept further requests.

In both cases, the {ref}`Jina Client <client>` raises an Exception.

### Terminate an Executor on certain errors

Some exceptions like network errors or request timeouts can be transient and can recover automatically. Sometimes fatal errors or user-defined errors put the Executor in an unusable state, in which case it can be restarted. Locally the Flow must be re-run manually to restore Executor availability. 

On Kubernetes deployments, this can be automated by terminating the Executor process, causing the Pod to terminate. The autoscaler restores availability by creating a new Pod to replace the terminated one. Termination can be enabled for one or more errors by using the `exit_on_exceptions` argument when adding the Executor to a Flow. When it matches the caught exception, the Executor terminates gracefully.
 
A sample Orchestration can be `Deployment(uses=MyExecutor, exit_on_exceptions: ['Exception', 'RuntimeException'])`. The `exit_on_exceptions` argument accepts a list of Python or user-defined Exception or Error class names.

## Network errors

When a {class}`~jina.Flow`'s gateway can't reach an {ref}`Executor or Head <architecture-overview>`, the Flow attempts to re-connect to the faulty deployment according to a retry policy. The same applies to calls to Executors that time out. The specifics of this policy depend on the Flow's environment, as outlined below.

````{admonition} Hint: Prevent Executor timeouts
:class: hint
If you regularly experience Executor call timeouts, set the Flow's `timeout_send` attribute to a larger value 
by setting `Flow(timeout_send=time_in_ms)` in Python
or `timeout_send: time_in_ms` in your Flow YAML with-block.

Neural network forward passes on CPU (and other unusually expensive operations) commonly lead to timeouts with the default setting.
````

````{admonition} Hint: Custom retry policy
:class: hint
You can override the default retry policy and instead choose a number of retries performed for each Executor
with `Flow(retries=n)` in Python, or `retries: n` in the Flow
YAML `with` block.
````

If, during the complete execution of this policy, no successful call to any Executor replica can be made, the request is aborted
and the failure is {ref}`reported to the client <failure-reporting>`.

### Request retries: Local deployment

If a Flow is deployed locally (with or without {ref}`containerized Executors <dockerize-exec>`), the following policy
for failed requests applies on a per-Executor basis:

- If there are multiple replicas of the target Executor, try each replica at least once, or until the request succeeds.
- Irrespective of the number of replicas, try the request at least three times, or until it succeeds. If there are fewer than three replicas, try them in a round-robin fashion.

### Request retries: Deployment with Kubernetes

If a Flow is {ref}`deployed in Kubernetes <kubernetes>` without a service mesh, retries cannot be distributed to different replicas of the same Executor.

````{admonition} See Also
:class: seealso

The impossibility of retries across different replicas is a limitation of Kubernetes in combination with gRPC.
If you want to learn more about this limitation, see [this](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/) Kubernetes blog post.

An easy way to overcome this limitation is to use a service mesh like [Linkerd](https://linkerd.io/).
````

Concretely, this results in the following per-Executor retry policy:

- Try the request three times, or until it succeeds, always on the same replica of the Executor

### Request retries: Deployment with Kubernetes and service mesh

A Kubernetes service mesh can enable load balancing, and thus retries, between an Executor's replicas.

````{admonition} Hint
:class: hint
While Jina supports any service mesh, the output of `f.to_kubernetes_yaml()` already includes the necessary annotations for [Linkerd](https://linkerd.io/).
````

If a service mesh is installed alongside Jina in the Kubernetes cluster, the following retry policy applies for each Executor:

- Try the request at least three times, or until it succeeds
- Distribute the requests to the replicas according to the service mesh's configuration


````{admonition} Caution
:class: caution

Many service meshes have the ability to perform retries themselves.
Be careful about setting up service mesh level retries in combination with Jina, as it may lead to unwanted behaviour in combination with
Jina's own retry policy.

Instead, you may want to disable Jina level retries by setting `Flow(retries=0)` in Python, or `retries: 0` in the Flow
YAML `with` block.
````

(failure-reporting)=
### Failure reporting

If the retry policy is exhausted for a given request, the error is reported back to the corresponding client.

The resulting error message contains the *network address* of the failing Executor.
If multiple replicas are present, all addresses are reported - unless the Flow is deployed using Kubernetes, in which
case the replicas are managed by Kubernetes and only a single address is available.

Depending on the client-to-gateway protocol, and the type of error, the error message is returned in one of the following ways:

**Could not connect to Executor:**

- **gRPC**: A response with the gRPC status code 14 (*UNAVAILABLE*) is issued, and the error message is contained in the `details` field.
- **HTTP**: A response with the HTTP status code 503 (*SERVICE_UNAVAILABLE*) is issued, and the error message is contained in `response['header']['status']['description']`.
- **WebSockets**: The stream closes with close code 1011 (*INTERNAL_ERROR*) and the message is contained in the WebSocket close message.

**Call to Executor timed out:**

- **gRPC**: A response with the gRPC status code 4 (*DEADLINE_EXCEEDED*) is issued, and the error message is contained in the `details` field.
- **HTTP**: A response with the HTTP status code 504 (*GATEWAY_TIMEOUT*) is issued, and the error message is contained in `response['header']['status']['description']`.
- **WebSockets**: The stream closes with close code 1011 (*INTERNAL_ERROR*) and the message is contained in the WebSockets close message.

For any of these scenarios, the {ref}`Jina Client <client>` raises a `ConnectionError` containing the error message.

## Debug via breakpoint

Standard Python breakpoints don't work inside `Executor` methods when called inside a Flow context manager. Nevertheless, `import epdb; epdb.set_trace()` works just like a native Python breakpoint. Note that you need to `pip install epdb` to access this type of breakpoints.


````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow, Executor, requests
 
class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        a = 25
        import epdb; epdb.set_trace() 
        print(f'\n\na={a}\n\n')
 
def main():
    f = Flow().add(uses=CustomExecutor)
    with f:
        f.post(on='')

if __name__ == '__main__':
    main()

```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow, Executor, requests
 
class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        a = 25
        breakpoint()
        print(f'\n\na={a}\n\n')
 
def main():
    f = Flow().add(uses=CustomExecutor)
    with f:
        f.post(on='')
 
if __name__ == '__main__':
    main()
```
````

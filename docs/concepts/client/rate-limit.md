(client-post-prefetch)=
# Rate Limit

There are two ways of applying a rate limit using the {class}`~jina.Client`. 
1. Set using the `Client` class constructor and defaults to 1,000 requests. 
1. Set the argument when using {meth}`~jina.clients.mixin.PostMixin.post` method. If not provided, the deafult value of
1,000 requests will be used. The method argument will override the argument provided in the `Client` class constructor.


The `prefetch` argument controls the number of in flight requests made by the {meth}`~jina.clients.mixin.PostMixin.post` 
method. Using the default value might overload the {class}`~jina.Flow` especially if the operation characteristics of the `Flow` 
are unknown. Furthermore the Client can send various types of requests which can have varying resource usage in the `Flow`.

For example, a high number of `index` requests can contain a large data payload requiring high input/output operation.
This increases CPU consumption and eventually lead to a build up of the requests on the Flow. If the queue of in flight requests 
is already large, a very light weight `search` request to return the total number of 
Documents in the index might be blocked until the queue of `index` requests can be completely processed. To prevent such a scenario,
apply the `prefetch` value on the {meth}`~jina.clients.mixin.PostMixin.post` method to limit the rate of
requests for expensive operations.

Apply the `prefetch` argument on the {meth}`~jina.clients.mixin.PostMixin.post` method to dynamically increase 
the `Flow` responsiveness for customer-facing requests which require faster response times vs. background requests such as cronjobs or 
analytics requests which can be processed slowly.

```python
from jina import Client

client = Client()

# uses the default limit of 1,000 requests
search_responses = client.post(...)

# sets a hard limit of 5 in flight requests
index_responses = client.post(..., prefetch=5)
```

A global rate limit on the {class}`~jina.Gateway` can also be set using the {ref}`prefetch <prefetch>` option in the `Flow`. 
This argument however serves as a global rate limit and cannot be customized based on the request workload. The `prefetch` 
argument for the `Client` serves as a class level rate limit for all requests made from the client. The `prefetch`
argument for the {meth}`~jina.clients.mixin.PostMixin.post` method serves as a method level overriding the arguments at the
`Client` and the `Flow`.
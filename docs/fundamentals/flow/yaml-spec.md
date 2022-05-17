(flow-yaml-spec)=
# YAML specification

This page outlines the specification for valid Flow YAML files.
Such YAML configurations can be used to generate a Flow via `Flow.load_config('flow.yml')`.

## Example

The following constitutes a typical Flow configuration:

`flow.yml`/`flow.yaml`:
```yaml
jtype: Flow
version: '1'
with:
  protocol: http
executors:
  - uses:
    jtype: CustomizedEncoder
    when:
        tags__key:
            $eq: 5
  - uses:
    jtype: BaseExecutor
    metas:
      name: test_indexer
      workspace: ./indexed
```

## Fields

- `jtype`
String that is always set to "Flow", indicating the corresponding Python class

- `with`
Keyword arguments passed to the Flow `__init__()` method.
  - `protocol` String indicating the networking protocol used by the Flow's gateway. Can be "http", "grpc", or "websocket".
  - `no_nebug_endpints` Boolean that disables default debug endpoints on the Flow's gateway.
  - `no_crud_endpoints` Boolean that disables default CRUD endpoints on the Flow's gateway.
  - `cors` Boolean that enables [Cross Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS).
  - `expose_graphql_endpont` Boolean that enables GraphQL. Only available if `protocol` is "http".
  - `ssl_certfile` Path to SSL certfile. If both `ssl_certfile` and `ssl_keyfile` are provided, SSL will be enabled.
  - `ssl_keyfile` Path to SSL keyfile. If both `ssl_certfile` and `ssl_keyfile` are provided, SSL will be enabled.
  - `prefetch` Integer limiting how many concurrent requests the Flow will accept. Default is disabled.
  - `timeout_send` Integer limiting the maximum time allowed for a single request to be processed, in milliseconds. Default is disabled.
  - `monitoring` Boolean that enables monitoring of the Flow via Prometheus stack.
  - `port_monitoring` Integer that specifies the port on which Prometheus exposes its metrics server for the Flow Gateway.
  - 

- `version`
String indicating the version of the Flow

- `executors`
Collection of Executors used in the Flow. A specification of valid Executor configurations can be found {ref}`here <executor-yaml-spec>`.
Additionally, the following fields can be specified under this collection:
  - `when` Collection of input filter conditions according to [this syntax](https://docarray.jina.ai/fundamentals/documentarray/find/?highlight=filter&utm_source=docarray#filter-with-query-operators).
  - `monitoring` Boolean that can be used to disable monitoring for this Executor. Default follows the Flow's `monitoring` property.
  - `port_monitoring` Integer that specifies the port on which Prometheus exposes its metrics server for this Executor, if monitoring is enabled.

- `metas`
Collection that overrides the `metas` attribute for all Executors in a Flow.
- This can be useful when loading multiple Executors from the same Python file.
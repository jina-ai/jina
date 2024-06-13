(gateway-yaml-spec)=
# {octicon}`file-code` YAML specification

This page outlines the specification for Gateway.

Gateway config is nested under the `gateway` section of a Flow YAML. For example,

```{code-block} yaml
---
emphasize-lines: 3-4
---
jtype: Flow
version: '1'
gateway:
  protocol: http
```

Defines a Gateway that uses HTTP protocol.

```{warning}
It is also possible to define a Gateway configuration directly under the top-level `with` field, but it is not recommended.
```

## Fields

The following fields are defined for Gateway and can be set under the `gateway` section (or the `with` section) of a Flow YAML.

```{include} ../flow/gateway-args.md
```

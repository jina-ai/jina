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
It is also possible to define a Gateway configuration under the Flow `with` key.
## Fields

The following fields are defined for Gateway and can be set under the `gateway` section (or the `with` section) of a Flow YAML.

```{include} ../flow/gateway-args.md
```

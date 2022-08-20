(gateway-yaml-spec)=
# {octicon}`file-code` YAML specification

This page outlines the specification for Gateway.

Gateway config is nested under `with` key of a Flow YAML. For example,

```{code-block} yaml
---
emphasize-lines: 3-4
---
jtype: Flow
version: '1'
with:
  protocol: http
```

Defines a Gateway that uses HTTP protocol.

## Fields

The following fields are defined for Gateway and can be set under `with` key of a Flow YAML.

```{include} ../flow/gateway-args.md
```

# {octicon}`file-code` YAML specification

YAML is widely used in Jina to define an Executor, Flow, Gateway, Hub manifest and JCloud. This page helps you navigate different YAML specifications.

:::::{grid} 2
:gutter: 3


::::{grid-item-card} Executor YAML
:link: fundamentals/executor/yaml-spec
:link-type: doc

Define the argument of `__init__`, Python module dependencies and other settings of an Executor. 
::::

::::{grid-item-card} Flow YAML
:link: fundamentals/flow/yaml-spec
:link-type: doc

Define the Executors, the topology and the Gateway settings of a Flow.
::::

::::{grid-item-card} Gateway YAML
:link: fundamentals/gateway/yaml-spec
:link-type: doc

Define the protocol, TLS, authentication and other settings of a Gateway.

::::

::::{grid-item-card} Hub Manifest YAML
:link: fundamentals/executor/hub/create-hub-executor
:link-type: doc

Define how the Executor appears in the Hub.

::::


::::{grid-item-card} JCloud YAML
:link: fundamentals/jcloud/resources
:link-type: doc

Define the resources and autoscaling settings on Jina Cloud

::::



:::::

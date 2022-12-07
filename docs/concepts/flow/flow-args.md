| Name | Description | Type | Default |
|----|----|----|----|
| `name` | The name of this object.<br><br>    This will be used in the following places:<br>    - how you refer to this object in Python/YAML/CLI<br>    - visualization<br>    - log message header<br>    - ...<br><br>    When not given, then the default naming strategy will apply. | `string` | `None` |
| `workspace` | The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`. | `string` | `None` |
| `log_config` | The YAML config of the logger used in this object. | `string` | `default` |
| `quiet` | If set, then no log will be emitted from this object. | `boolean` | `False` |
| `quiet_error` | If set, then exception stack information will not be added to the log | `boolean` | `False` |
| `uses` | The YAML path represents a flow. It can be either a local file path or a URL. | `string` | `None` |
| `restart` | If set, the Flow will restart while blocked if the YAML configuration source is changed. | `boolean` | `False` |
| `env` | The map of environment variables that are available inside runtime | `object` | `None` |
| `inspect` | The strategy on those inspect deployments in the flow.<br><br>    If `REMOVE` is given then all inspect deployments are removed when building the flow. | `string` | `COLLECT` |
(manifest-yaml)=
# {octicon}`file-code` YAML specification

`manifest.yml` is an optional file that shipped with your Executor bundle. It annotates your Executor with meta information so that it can be better managed by the Hub system. 

To get better appealing on Jina Hub, you may want to 
carefully set `manifest.yml` to the correct values:

| Key                | Description                                                                                | Default |
| ---                | ---                                                                                        | ---     |
| `manifest_version` | The version of the manifest protocol                                                       | `1`     |
| `name`             | Human-readable title of the Executor                                                       | None    |
| `description`      | Human-readable description of the Executor                                                 | None    |
| `url`              | URL to find more information about the Executor, normally the GitHub repo URL              | None    |
| `keywords`         | A list of strings to help users filter and locate your package                             | None    |

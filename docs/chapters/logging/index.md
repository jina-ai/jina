# Logging configuration in jina

**Logging** (beta)
In order to better understand and monitor the running and lifetime of Jina's flow, peas and pods, jina logs messages
in 6 different levels (DEBUG, INFO, WARNING, ERROR, CRITICAL, SUCCESS). The default level is controlled by 'JINA_LOG_VERBOSITY' environment variable.

Jina uses loggers from logging python library with different Handlers to control where the messages are sent/stored:

- `ConsoleHandler`. By default, logger uses a `ConsoleHandler` to print the logs in each Pea's local stdout.
- `FileHandler`. Jina offers the possibility to put the logs in local files either as simple text or as json format
 if `JINA_LOG_FILE` environment variable is set to `TXT` or `JSON`.
- `FluentDHandler`. Given the distributed nature of Jina's Peas and Pods, Jina offers a flexible solution that lets the user configure
how and where the logs are forwarded. This is specially useful for log analytics such as the one offered by [dahsboard](https://dashboard.jina.ai/).
This is active when `log_sse` is provided as argument to the Peas.
 
For some specific information, Jina also uses a `ProfileLogger` that uses `FluentDHandler` to log profiling information.

## FluentD
Fluentd is an open source data collector for unified logging layer [https://www.fluentd.org/](https://www.fluentd.org/).

Fluentd is expected to be used as a daemon receiving messages from the Jina logger and forwarding them to specific outputs using its
output plugins and configurations. 
 
Although fluentd can be configured to forward logs to the user's preferred destinations, Jina offers a default configuration under `/resources` folder which expects a fluentd daemon to be running
inside every machine running a jina instance or Pea. Then the default configuration must be adapted to send the logs to the specific server 
where the Flow and the dashboard will be run. (This default behavior will evolve)

See default `fluent.conf` configuration provided by jina. It takes every input coming in the listening 24224 port and 
depending on the kind of message, sends it to a local temporary file, from where the Flow will read the incoming file (beta version).

```xml
<source>
  @type forward
  @id http_input

  port 24224
</source>

## match tag=myapp.** and forward and write to file in local
<match jina.**>
  @type file
  path /tmp/jina-log
  append true
  <buffer>
      @type file
      flush_mode interval
      flush_interval 1s
  </buffer>
</match>

<match jina-profile.**>
  @type file
  path /tmp/jina-profile
  append true
  <buffer>
      @type file
      flush_mode interval
      flush_interval 1s
  </buffer>
</match>
```

This is the default configuration, that works well together with the configuration provided in `logging.fluentd.yml`,
which controls the tags assigned to the different type of logs, as well as the host and port where the handler will send the 
logs. By default it expects a fluentd daemon to run in every local and remote Pea (this is the most scalable configuration)

```yaml
# this configuration describes where is the fluentD daemon running and waiting for logs to be emitted.
# FluentD then will have its own configuration to forward the messages according to its own syntax
# prefix will help fluentD filter data. This will be prepended for FluentD to easily filter incoming messages
tag: jina
profile-tag: jina-profile
host: 0.0.0.0
port: 24224
``` 

To better understand fluentd configuration and to see how you can adapt to your needs, please see [https://docs.fluentd.org/configuration](https://docs.fluentd.org/configuration)

## Start fluentd daemon
For the logging using fluentd to work and therefore for the dashboard to properly have access to the logs, the user needs to
start fluentd daemon. It can be done in every remote and local machine or just in the host where the FluentDHandler will send the logs.

- Install [https://docs.fluentd.org/installation](https://docs.fluentd.org/installation)
- Run `fluentd -c ${FLUENTD_CONF_FILE}` (Default conf file `${JINA_RESOURCES_PATH}/fluent.conf`)
)

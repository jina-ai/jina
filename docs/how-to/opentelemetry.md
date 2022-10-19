(opentelemetry)=
# Observability and Instrumentation with OpenTelemetry and Jina

There are two major setups required to visualize/monitor your applications signals using [OpenTelemetry](https://opentelemetry.io). The first step is covered by Jina which integrates the [OpenTelemetry API and SDK](https://opentelemetry-python.readthedocs.io/en/stable/api/index.html) at the application level. The {ref}`Flow Instrumentation <instrumenting-flow>` page covers in detail the steps required to enable OpenTelemetry in a Flow. A {class}`~jina.Client` can also be instrumented which is documented in the {ref}`Client Instrumentation <instrumenting-client>` section.

In this section we will dive into the OpenTelemetry infrastructure setup required to collect, store and visualize the traces and metrics data exported by the Pods. This setup is the users responsibility and this section will only serve as the initial/introductory guide to running OpenTelemetry infrastructure components. 

Since OpenTelemetry is opensource and is mostly responsible for the API standards and specification, there are various providers that implement the specification. This section follows the default recommendations from the OpenTelemetry documentation that also fits into the Jina implementations.

## Exporting traces and metrics data

Pods created using a {class}`~jina.Flow` with tracing or metrics enabled use the [SDK Exporters](https://opentelemetry.io/docs/instrumentation/python/exporters/) to send the data to a central [Collector](https://opentelemetry.io/docs/collector/) component which can be used to process the data further and store the data for visualization and alerting purposes. 

The push/export based mechanism also allows the application to start pushing data immediately on start up. This differs from the pull based mechanism wherein a separate scraping registry to discovery service is needed to identify data scraping targets.

At the moment Jina supports the configuration of the exporter backend host and port using the `traces_exporter_host`, `traces_exporter_port`, `metrics_exporter_host` and `metrics_exporter_port. Even though the Collector is metric data type agnostic (can accept any type of OpenTelemetry API data model), we provide separate configuration for Tracing and Metrics to allow users more flexibility in choosing their infrastructure components.

The `OTLPSpanExporter` and `OTLPMetricExporter` is provided by Jina as the default exporter implementation. The exporters also use the gRPC data transfer protocol. The following environment variables can be used to further configure the exporter client based on your requirement. The full list of exporter related environment variables are documented by the [PythonSDK library](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html). Apart from the `OTEL_EXPORTER_OTLP_PROTOCOL` and the `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` environment variables, all other library version specific environment variables can be used to configure the exporter clients.


## Collector

The [Collector](https://opentelemetry.io/docs/collector/) is a huge ecosystem of components that support various features such as scraping, collecting, processing and further exporting data to storage backends. The collector also can itself expose endpoints to allow scraping data. It is recommended to read the official documentation to understand the the full set of features and configuration required to run a Collector. The below section describes the minimum number of components and the respective configuration required for operating with Jina.

We recommend using the [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) from the contrib repository. We also use
- [Jaeger](https://www.jaegertracing.io) for collecting traces, visualizing tracing data and alerting based on tracing data.
- [Prometheus](https://prometheus.io) for collecting metric data and/or alerting.
- [Grafana](https://grafana.com) for visualizing data from Prometheus/Jaeger and/or alerting based on the data queried.

```{hint}
The Jaeger provides a comprehensive out of the box tools for end-to-end tracing monitoring, visualization and alerting. Other tools can also be substituted to achieve the necessary goals of observability and perfomance analysis. The same can be said for Prometheus and Grafana.
```

### Docker Compose

A minimal docker-compose.yml file can look like:

```yml
version: "3"
services:
  # Jaeger
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"

  otel-collector:
    image: otel/opentelemetry-collector:0.61.0
    command: [ "--config=/etc/otel-collector-config.yml" ]
    volumes:
      - ${PWD}/otel-collector-config.yml:/etc/otel-collector-config.yml
    ports:
      - "8888" # Prometheus metrics exposed by the collector
      - "8889" # Prometheus exporter metrics
      - "4317:4317" # OTLP gRPC receiver
    depends_on:
      - jaeger

  prometheus:
    container_name: prometheus
    image: prom/prometheus:latest
    volumes:
      - ${PWD}/prometheus-config.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    container_name: grafana
    image: grafana/grafana-oss:latest
    ports:
      - 3000:3000
```

The corresponding OpenTelemetry Collector configuration below needs to be stored in file *otel-collector-config.yml*.
```yml
receivers:
  otlp:
    protocols:
      grpc:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:8889"
    # can be used to add additional labels
    const_labels:
      label1: value1

processors:
  batch:

service:
  extensions: []
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger]
      processors: [batch]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

Briefly, this setup creates a gRPC Collector Receiver on port 4317 that can collect data pushed by the Flow Pods. Collector exporters for Jaeger and Prometheus backends are configured to export tracing and metrics data respectively. The final **service** section creates a collector pipeline combining the receiver (collect data), export (to backend), process (batching) sub components.

The Prometheus minimal configuraton below needs to be stored in file *prometheus-config.yml*.
```yml
scrape_configs:
  - job_name: 'otel-collector'
    scrape_interval: 500ms
    static_configs:
      - targets: ['otel-collector:8889']
      - targets: ['otel-collector:8888']
```

The Prometheus configuration now need only scrape from the OpenTelemetry Collector to get all the data from OpenTelemetry Metrics instrumented applications.


### Running a Flow locally

Run the Flow and a sample reqeust that we want to instrument locally. If the backends are running successfully the Flow has exported data to the Collector which can be queries and viewed which will be discussed next.

```python
from jina import Flow, Document, DocumentArray

with Flow(
    tracing=True,
    traces_exporter_host='localhost',
    traces_exporter_port=4317,
    metrics=True,
    metrics_exporter_host='localhost',
    metrics_exporter_port=4317,
).add(uses='jinahub://SimpleIndexer') as f:
    f.post('/', DocumentArray([Document(text='hello')]))
```

## Viewing Traces in Jaeger UI

The Jaeger UI can be opened by visiting this [url](http://localhost:16686). More details and guides on navigating the Jaeger UI can be found in the official [docs](https://www.jaegertracing.io/docs/1.38/external-guides/#using-jaeger).

```{hint}
The list of available traces are documented in the {ref}`Flow Instrumentation <instrumenting-flow>` section.
```

## Monitor with Prometheus and Grafana

External entities (like Grafana) can access these aggregated metrics via the query language [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/) and let users visualize the metrics with dashboards. Comprehensive tutorial can be found [here](https://prometheus.io/docs/visualization/grafana/).

```{hint}
The list of available metrics are documented in the {ref}`Flow Instrumentation <instrumenting-flow>` section.
```

## JCloud Support

Currenlty OpenTelemetry is not supported by JCloud. The features will be made available soon. Until then the deprecated Promtheus based {ref}`monitoring setup <monitoring-flow>` can be used.

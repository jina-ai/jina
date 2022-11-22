(opentelemetry-migration)=
# Migrate from Prometheus/Grafana to OpenTelemetry/Prometheus/Grafana 

The {ref}`Prometheus/Grafana <monitoring>` based monitoring setup will soon be deprecated in favor of the {ref}`OpenTelemetry setup <opentelemetry>`. This section provides the details required to update/migrate your Prometheus configuration and Grafana dashboard to continue monitoring with OpenTelemetry. Refer to {ref}`Opentelemetry setup <opentelemetry>` for the new setup before proceeding further.

```{hint}
:class: seealso
Refer to {ref}`Prometheus/Grafana-only <monitoring>` section for the soon to be deprecated setup.
```

## Update Prometheus configuration

With a Prometheus-only setup, you need to set up a `scrape_configs` configuration or service discovery plugin to specify the targets for pulling metrics data. In the OpenTelemetry setup, each Pod pushes metrics to the OpenTelemetry Collector. The Prometheus configuration now only needs to scrape from the OpenTelemetry Collector to get all the data from OpenTelemetry-instrumented applications.

The new Prometheus configuration for the `otel-collector` Collector hostname is:

```yaml
scrape_configs:
  - job_name: 'otel-collector'
    scrape_interval: 500ms
    static_configs:
      - targets: ['otel-collector:8888'] # metrics from the collector itself
      - targets: ['otel-collector:8889'] # metrics collected from other applications
```

## Update Grafana dashboard

The OpenTelemetry [Histogram](https://opentelemetry.io/docs/reference/specification/metrics/api/#histogram) provides quantile window buckets automatically (unlike the Prometheus [Summary](https://prometheus.io/docs/concepts/metric_types/#summary) instrument). You need to manually configure the required quantile window. The quatile window metric will then be available as a separate time series metric.

In addition, the OpenTelemetry `Counter/UpDownCounter` instruments do not add the `_total` suffix to the base metric name.

To adapt Prometheus queries in Grafana:
- Use the [histogram_quantile](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile) function to query the average or desired quantile window time series data from Prometheus. For example, to view the 0.99 quantile of the `jina_receiving_request_seconds` metric over the last 10 minutes, use query `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[10m]))`.
- Remove the `_total` prefix from the Counter/UpDownCounter metric names.

You can download a [sample Grafana dashboard JSON file](https://github.com/jina-ai/example-grafana-prometheus/blob/main/grafana-dashboards/flow-histogram-metrics.json) and import it into Grafana to get started with some pre-built graphs.

```{hint}
A list of available metrics which will soon be deprecated is in the {ref}`Flow Monitoring <monitoring-flow>` section.
A list of available metrics is in the {ref}`Flow Instrumentation <instrumenting-flow>` section.
```
from jina import __default_port_monitoring__


class MonitoringMixin:
    """The Monitoring Mixin for pods"""

    def _setup_monitoring(self):
        """
        Wait for the monitoring server to start
        """

        if self.args.monitoring:
            from prometheus_client import CollectorRegistry

            self.metrics_registry = CollectorRegistry()
        else:
            self.metrics_registry = None

        if self.args.monitoring:

            from prometheus_client import start_http_server

            try:
                start_http_server(
                    self.args.port_monitoring, registry=self.metrics_registry
                )
            except OSError as e:
                if (
                    e.args[0] == 98
                    and self.args.port_monitoring == __default_port_monitoring__
                ):
                    self.logger.warning(
                        f'The port monitoring {self.args.port_monitoring} is already in use. If you are running Jina '
                        f'Flow natively, you may have not set different ports for each Executor'
                    )
                    raise
                else:
                    raise

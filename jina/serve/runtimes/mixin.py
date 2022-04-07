import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


def _start_monitoring_server(port, registry: 'CollectorRegistry', addr=''):
    """Starts a WSGI server for prometheus metrics as a daemon thread.
    :param port: port on which to expose
    :param registry: prometheus registry that will feed to http server with metrics
    :param addr: address on which to expose
    :return: httpd server
    """
    from wsgiref.simple_server import make_server

    from prometheus_client import make_wsgi_app
    from prometheus_client.exposition import ThreadingWSGIServer, _SilentHandler

    app = make_wsgi_app(registry)
    httpd = make_server(
        addr, port, app, ThreadingWSGIServer, handler_class=_SilentHandler
    )
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()

    return httpd


def _close_monitoring_server(httpd):
    t = threading.Thread(target=httpd.shutdown())
    t.daemon = True
    t.start()


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

            self.httpd_monitoring = _start_monitoring_server(
                self.args.port_monitoring, registry=self.metrics_registry
            )

    def teardown_monitoring(self):
        """clean up monitoring resources during teardown."""
        if self.args.monitoring:
            _close_monitoring_server(self.httpd_monitoring)

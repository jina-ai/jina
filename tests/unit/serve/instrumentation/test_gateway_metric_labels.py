from jina import Executor, Flow, requests, DocumentArray


def test_gateway_metric_labels(monkeypatch_metric_exporter):
    collect_metrics, read_metrics = monkeypatch_metric_exporter

    class FirstExec(Executor):
        @requests()
        def meow(self, docs, **kwargs):
            return DocumentArray.empty(3)

    class SecondExec(Executor):
        @requests()
        def meow(self, docs, **kwargs):
            return DocumentArray.empty(3)

    with Flow(
        tracing=False,
        metrics=True,
        metrics_exporter_host='localhost',
        metrics_exporter_port=4317,
        port=12345,
    ).add(name='first_exec', uses=FirstExec).add(
        name="second_exec", uses=SecondExec
    ) as f:
        f.post('/')
        f.plot('flow.png')

        collect_metrics()
        metrics = read_metrics()
        gateway_metrics = metrics['gateway/rep-0'][0]['resource_metrics'][0][
            'scope_metrics'
        ][0]['metrics']
        gateway_metric_data_point = {
            i['name']: i['data']['data_points'] for i in gateway_metrics
        }

        assert (
            'address'
            in gateway_metric_data_point['jina_sending_request_seconds'][0][
                'attributes'
            ]
        )
        assert (
            'address'
            in gateway_metric_data_point['jina_sent_request_bytes'][0]['attributes']
        )
        assert (
            'address'
            in gateway_metric_data_point['jina_received_response_bytes'][0][
                'attributes'
            ]
        )
        assert (
            'address'
            in gateway_metric_data_point['jina_sending_request_seconds'][1][
                'attributes'
            ]
        )
        assert (
            'address'
            in gateway_metric_data_point['jina_sent_request_bytes'][1]['attributes']
        )
        assert (
            'address'
            in gateway_metric_data_point['jina_received_response_bytes'][1][
                'attributes'
            ]
        )

        assert (
            'deployment'
            in gateway_metric_data_point['jina_sending_request_seconds'][0][
                'attributes'
            ]
        )
        assert (
            'deployment'
            in gateway_metric_data_point['jina_sent_request_bytes'][0]['attributes']
        )
        assert (
            'deployment'
            in gateway_metric_data_point['jina_received_response_bytes'][0][
                'attributes'
            ]
        )
        assert (
            'deployment'
            in gateway_metric_data_point['jina_sending_request_seconds'][1][
                'attributes'
            ]
        )
        assert (
            'deployment'
            in gateway_metric_data_point['jina_sent_request_bytes'][1]['attributes']
        )
        assert (
            'deployment'
            in gateway_metric_data_point['jina_received_response_bytes'][1][
                'attributes'
            ]
        )

        assert (
            gateway_metric_data_point['jina_received_response_bytes'][0]['attributes'][
                'deployment'
            ]
            == 'first_exec'
        )
        assert (
            gateway_metric_data_point['jina_received_response_bytes'][1]['attributes'][
                'deployment'
            ]
            == 'second_exec'
        )

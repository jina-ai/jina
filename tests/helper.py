def _validate_dummy_custom_gateway_response(port, expected):
    import requests

    resp = requests.get(f'http://127.0.0.1:{port}/').json()
    assert resp == expected


def _validate_custom_gateway_process(port, text, expected):
    import requests

    resp = requests.get(f'http://127.0.0.1:{port}/stream?text={text}').json()
    assert resp == expected

from pathlib import Path

from daemon.models import DeploymentModel

cur_dir = Path(__file__).parent
api = '/deployment'


def test_deployment_api(partial_deployment_client):
    deployment_model = DeploymentModel()

    response = partial_deployment_client.post(
        api,
        json={
            'deployment': deployment_model.dict(exclude={'log_config'}),
            'envs': {'key1': 'val1'},
        },
    )
    assert response

    response = partial_deployment_client.get(api)
    assert response

    assert response.json()['arguments']['port_jinad'] == deployment_model.port_jinad

    response = partial_deployment_client.delete(api)
    assert response

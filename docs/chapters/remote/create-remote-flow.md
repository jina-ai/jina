# Creating a Remote Flow with jinad

One common use case in production is running the whole Flow on the remote with pods distributed on different machines. In this case, the very first thing is to ensure all the remote machines have `jinad` running properly. We will see how to create a remote Flow from the local machine.

## Prerequisites
Before the start, make sure you have read the [prerequisites for using jinad](https://docs.jina.ai/chapters/remote/jinad.html#prerequisites)

## Steps
### 1. Create a Flow 
As `jinad` hosts a service on the remote, we can use the `jinad` API `/flow/yaml` to create a Flow via uploading a Flow configuration yaml file. Please refer to the full  [API specifications](https://api.jina.ai/daemon/) for more details.

```python
import requests

def create_flow(flow_url, yamlspec):
    flow_creation_api = f'{flow_url}/flow/yaml/'
    with open(yamlspec, 'rb') as f:
        files = [('yamlspec', f)]
        try:
            r = requests.put(url=flow_creation_api, files=files, timeout=10)
            if r.status_code == requests.codes.ok:
                return r.json()['flow_id']
            else:
                print('Remote Flow creation failed')
        except requests.exceptions.RequestException as ex:
            print(f'Exception raised: {ex!r}')

if __name__ == '__main__':
    host_ip = '3.16.166.3'
    jinad_port = '8000'
    flow_api = f'http://{host_ip}:{jinad_port}'
    flow_id = create_flow(flow_api, 'dummy_flow.yml')
    print(f'flow is created: {flow_id}')
```

We use a dummy Flow configuration `dummy_flow.yml` as below for demo purpose.

```yaml
!Flow
version: 1
pods:
  - name: pod0
    method: add
    uses: _logforward
  - name: pod1
    method: add
    uses: _logforward
```

After running the above codes, we print out the flow id and please note this flow id for the next step. 

```text
flow is created: cdd53e16-5575-11eb-86b2-0ab9db700358
```

### 2. Check Flow Status
Before using the Flow we created, we need to get detail information about the Flow so that we can send queries to the Flow. To get the information of the Flow, we can use the following scripts to retrieve the information from `/flow/cdd53e16-5575-11eb-86b2-0ab9db700358`

```python
import requests

def get_flow_info(flow_url, flow_id):
    flow_info_api = f'{flow_url}/flow/{flow_id}'
    try:
        r = requests.get(url=flow_info_api)
        if r.status_code == requests.codes.ok:
            return str(r.json()["port"])
        else:
            print('Remote Flow info retrieval failed')
    except requests.exceptions.RequestException as ex:
        print(f'Exception raised: {ex!r}')

def main():
    host_ip = '12.34.56.78'
    jinad_port = '8000'
    flow_api = f'http://{host_ip}:{jinad_port}'
    flow_id = 'cdd53e16-5575-11eb-86b2-0ab9db700358'
    flow_port = get_flow_info(flow_api, flow_id)
    print(f'Flow serves at {host_ip}:{flow_port}')
``` 

### 3. Run Index/Query via client 
With the host and port information of the remote Flow, we can use the gRPC client of jina to send index or query requests.

```python
from jina.parsers import set_client_cli_parser
from jina.clients import Client
from jina import Document

def send_index_request(host, port):
    print(f'index request sent to {host}:{port}')
    args = set_client_cli_parser().parse_args(
        ['--host', host, '--port-expose', str(port)])
    grpc_client = Client(args)
    grpc_client.index(
        [Document(text='hello, jina'), ], on_done=print)

def main():
    host_ip = '12.34.56.78'
    flow_port = '51871'
    send_index_request(host_ip, flow_port)
``` 

### 4. Terminate Flow
After getting all the work done, we terminate the Flow by sending a `DELETE` request to the `/flow` API.

```python
import requests

def delete_flow(flow_api, flow_id):
    flow_deletion_api = f'{flow_api}/flow?flow_id={flow_id}'
    try:
        r = requests.delete(url=flow_deletion_api)
        if r.status_code == requests.codes.ok:
            print('Remote Flow deletion succeeded')
        else:
            print('Remote Flow deletion failed')
    except requests.exceptions.RequestException as ex:
        print(f'Exception raised: {ex!r}')


def main():
    host_ip = '12.34.56.78'
    jinad_port = '8000'
    flow_id = 'cdd53e16-5575-11eb-86b2-0ab9db700358'
    flow_api = f'http://{host_ip}:{jinad_port}'
    delete_flow(flow_api, flow_id)
```
## What's next?

You many also want to check out the following articles.
[Creating a Remote Pod from Console](https://docs.jina.ai/chapters/remote/create-remote-pod-console-jinad.html)
[Creating a Remote Pod via Flow APIs](https://docs.jina.ai/chapters/remote/create-remote-pod-flow.html) 

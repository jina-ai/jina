# Kubernetes MVP Feature
This module contains WIP for developing the new kubernetes deployment support. 

The relevant code lives in this module and the [Flow Base](../../../flow/base.py).
To start experimenting, install a kubernetes cluster on GCP and get credential to your local machine.
I.e. `kubectl get nodes` should work. 

## Build the gateway docker file and push to GCP.

Clone this [repo](https://github.com/jina-ai/kubernetes_deployment) build the docker file and push it to your gcp 
container registry. Make sure to tag the image correctly with gcr.io/{project-id}/generic-gateway
You need to adapt the reference to this image in the [Flow Base](../../../flow/base.py).
```
kubernetes_tools.create(
    'deployment',
    {
        'name': 'gateway',
        'replicas': 1,
        'port': 8080,
        'command': "[\"python\"]",
        'args': f"[\"gateway.py\", \"{gateway_yaml}\"]",
        'image': 'gcr.io/{project-id}/generic-gateway',
        'namespace': namespace,
    },
)
```
I.e. the gateway deployment needs to refer to your docker image, otherwise you will run into ImagePullError.

## Install a nginx controller (requires helm)

````
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx
````

Get the external ip of the ingress controller (might take a couple of seconds after installation)
````
kubectl get service nginx-ingress-ingress-nginx-controller 
````

More Information on nginx controller on gke: https://cloud.google.com/community/tutorials/nginx-ingress-gke

## Install the demo flow

To deploy a flow, run [k8s-deploy.py](k8s-client.py).

## Make test request

To send test request to the client, run (k8s-client.py). Make sure to fill in the IP of your nginx controller.
kubectl create namespace postgres
kubectl create -f postgres-configmap.yml --namespace postgres
kubectl create -f postgres-storage.yml --namespace postgres
kubectl create -f postgres-deployment.yml --namespace postgres
kubectl create -f postgres-service.yml --namespace postgres

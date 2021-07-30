kubectl create namespace postgres
kubectl create -f postgres-configmap.yml
kubectl create -f postgres-pv.yml
kubectl create -f postgres-pvc.yml
kubectl create -f postgres-deployment.yml
kubectl create -f postgres-service.yml
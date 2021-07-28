echo "delete name space"
kubectl delete ns f1
echo "deploy cluster"
python k8s-deploy.py
echo "port forward"
kubectl port-forward svc/gateway-exposed -n f1 8080

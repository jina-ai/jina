
echo "delete search deployment"
kubectl delete deployment -n search-flow searcher1-pea-0
kubectl delete deployment -n search-flow searcher1-pea-1
kubectl delete deployment -n search-flow searcher2-pea-0
kubectl delete deployment -n search-flow searcher2-pea-1



#echo "delete name space"
#kubectl delete ns index-flow
#kubectl delete ns search-flow
#echo "deploy cluster"
#python jina/kubernetes/k8s-deploy.py
#echo "port forward"
#kubectl port-forward svc/postgres 5432 -n postgres &
#kubectl port-forward svc/gateway-exposed -n search-flow 8080




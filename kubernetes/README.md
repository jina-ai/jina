# Running jina demo on kubernetes

- kubectl apply https://raw.githubusercontent.com/longwuyuan/jina/master/kubernetes/manifests/jina-k8s.yaml

- kubectl port-forward service/jina-k8s 12345:12345

- In your browser, open the URL http://localhost:12345

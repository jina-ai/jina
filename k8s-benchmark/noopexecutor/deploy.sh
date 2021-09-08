# you can modify this and push to a custom repo

#GCP_PROJECT_NAME=mystical-sweep-320315
GCP_PROJECT_NAME=jina-showcase

registry=gcr.io/${GCP_PROJECT_NAME}/noop-executor

#registry=jinaaitmp/postgresdump

docker build -t noop-executor . --no-cache
docker tag noop-executor ${registry}
docker push ${registry}











#
#GCP_PROJECT_NAME=jina-showcase
#registry=gcr.io/${GCP_PROJECT_NAME}/florian-base
#docker tag florian-base ${registry}
#docker push ${registry}
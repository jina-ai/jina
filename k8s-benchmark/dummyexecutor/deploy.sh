# you can modify this and push to a custom repo

#GCP_PROJECT_NAME=mystical-sweep-320315
GCP_PROJECT_NAME=jina-showcase

registry=gcr.io/${GCP_PROJECT_NAME}/dummy-executor

#registry=jinaaitmp/postgresdump

docker build -t dummy-executor . --no-cache
docker tag dummy-executor ${registry}
docker push ${registry}











#
#GCP_PROJECT_NAME=jina-showcase
#registry=gcr.io/${GCP_PROJECT_NAME}/florian-base
#docker tag florian-base ${registry}
#docker push ${registry}
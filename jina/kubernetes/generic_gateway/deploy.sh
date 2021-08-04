# you can modify this and push to a custom repo

GCP_PROJECT_NAME=jina-showcase

docker build -t generic-gateway .
docker tag generic-gateway gcr.io/${GCP_PROJECT_NAME}/generic-gateway:latest
docker push gcr.io/${GCP_PROJECT_NAME}/generic-gateway:latest
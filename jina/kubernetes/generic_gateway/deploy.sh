# you can modify this and push to a custom repo
docker build -t generic-gateway .
docker tag generic-gateway gcr.io/jina-showcase/generic-gateway
docker push gcr.io/jina-showcase/generic-gateway
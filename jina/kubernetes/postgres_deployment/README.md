# Postgres Deployment

### Configuration
The config is stored in a [ConfigMap](postgres-configmap.yml)
and contains the credentials for the created database.

### Deploy
````shell
./deploy.sh
````

### Test Connection
Forward the port of the postgres service to your host and connect to the DB via psql.
```shell
kubectl port-forward -n postgres service/postgres 5432:5432 
psql -h localhost -U postgresadmin --password -p 5432 postgresdb 
```

### Clean Up
````
kubectl delete namespace postgres
````
The persistent volume needs to be deleted manually because it is not part of a namespace.
If you are just testing out things and need to re-deploy it is usually safe to keep the PV.


import sys

from workspace.postgres_indexer import PostgreSQLStorage
import json
print(sys.argv)

_, args = sys.argv

params = json.loads(args.replace('\'', '"'))

storage = PostgreSQLStorage(
    hostname=params['postgres_svc'],
    port=5432,
    username="postgresadmin",
    database="postgresdb",
    table=params['table_name'],
)
storage.dump(parameters={
    "dump_path": params['dump_path'],
    "shards": params['shards'],
})

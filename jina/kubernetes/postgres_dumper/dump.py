import os
import sys

os.chdir('/')
from workspace import PostgreSQLStorage


assert len(sys.argv) == 3
_, postgres_host, table_name, dump_path, num_shards = sys.argv

storage = PostgreSQLStorage(
    hostname=postgres_host,
    port=5432,
    username="postgresadmin",
    database="postgresdb",
    table=table_name,
)
storage.dump(parameters={
    "dump_path": dump_path,
    "shards": num_shards,
})

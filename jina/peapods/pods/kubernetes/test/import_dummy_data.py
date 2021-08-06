import os

os.chdir('/')
from workspace import PostgreSQLStorage

storage = PostgreSQLStorage(
    hostname="10.3.255.243",
    port=5432,
    username="postgresadmin",
    password="1235813",
    database="postgresdb",
    table="searcher1",
)
storage.dump(parameters={"dump_path": "/shared", "shards": 2})

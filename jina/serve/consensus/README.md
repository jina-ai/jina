# Raft implementation for Jina Docarray

## Setup Go

The default project and folder setup is for the Go project files. Install the Go version >= 1.19. To install all dependencies run:

```shell
go get
```

## Setup Python

A copy of the Jina library is placed under the `jina-core` folder. 
- Create a virtual environment with pipenv: 
```shell
pipenv --python 3.7
```
- Install Jina in the virtual environment:
```shell
pipenv install ".[devel]"
```
- To ensure that the correct jina binary is being used, run:
```shell
source $(pipenv --venv)/bin/activate
# check jina location
# the location should belong the the virtual env
which jina
```

## Create local protogen docker

A local docker version needs to be built to correctly re-build jina proto files if modified.

```shell
docker build -f Dockerfiles/protogen.Dockerfile -t proto/jina-raft-proto .
```

### Generate Proto for Python

```shell
docker run --rm -v $(pwd)/jina/proto:/jina/proto proto/jina-raft-proto
```

### Generate Proto for Go

```shell
scripts/protogen.sh
```

# Start Flows

Each flow needs to be started in a separate terminal.

```shell
scripts/start_executor.sh nodeA
scripts/start_executor.sh nodeB
scripts/start_executor.sh nodeC
```

## Delete Executor workspaces

```shell
scripts/delete_executor_workspaces.sh
```

# Install raftadmin locally

Due to the stale go version in the raftadmin repository, the `go install github.com/Jille/raftadmin` doesn't install the raftadmin binary. Follow the below steps to install the binary locally.

```shell
mkdir -p $GOPATH/src/github.com/Jille
cd $GOPATH/src/github.com/Jille
git clone github.com/Jille/raftadmin
go install cmd/raftadmin/raftadmin.go
ls $GOPATH/bin # the raftadmin binary should be available
```

# Create cluster workspace

```shell
rm -rf /tmp/jina-raft-cluster/node* && mkdir -p /tmp/jina-raft-cluster/node{A,B,C}
```

# Start your own cluster

```shell
go build # build a local binary executable
# open new terminal
scripts/start_nodeA.sh
# open new terminal
scripts/start_nodeB.sh
# open new terminal
scripts/start_nodeC.sh
# open new terminal
scripts/admin_add_nodes.sh
```

*Note: The `--raft_bootstrap` argument is required only for the first run when creating a cluster from scratch.*

### Execute a single request

```shell
go run client/client.go --target=localhost:50051
```

### Execute snapshot on a raft node

```shell
scripts/snapshot.sh
```

# Debugging scripts

### Executor snapshot and snapshot progress

To run a snapshot on the executor directly:
```shell
python scripts/trigger_executor_snapshot.py '0.0.0.0:60061'
```

To check the status of a snapshot with id '123' on the executor directly:
```shell
python scripts/check_snapshot_status.py '0.0.0.0:60061' '123'
```

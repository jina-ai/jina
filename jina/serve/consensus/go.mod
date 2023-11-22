module jraft

go 1.19

require (
	github.com/Jille/raft-grpc-leader-rpc v1.1.0
	github.com/Jille/raft-grpc-transport v1.1.1
	github.com/Jille/raftadmin v1.2.0
	github.com/golang/protobuf v1.5.3
	github.com/hashicorp/go-hclog v0.16.2
	github.com/hashicorp/raft v1.3.11
	github.com/hashicorp/raft-boltdb v0.0.0-20220329195025-15018e9b97e0
	//google.golang.org/grpc v1.47.5
	google.golang.org/protobuf v1.31.0
)

replace google.golang.org/grpc => /home/joan/workspace/grpc-go

require google.golang.org/grpc v1.59.0

require (
	github.com/armon/go-metrics v0.3.9 // indirect
	github.com/boltdb/bolt v1.3.1 // indirect
	github.com/fatih/color v1.12.0 // indirect
	github.com/hashicorp/go-immutable-radix v1.3.1 // indirect
	github.com/hashicorp/go-msgpack v0.5.5 // indirect
	github.com/hashicorp/golang-lru v0.5.4 // indirect
	github.com/mattn/go-colorable v0.1.8 // indirect
	github.com/mattn/go-isatty v0.0.17 // indirect
	golang.org/x/net v0.18.0 // indirect
	golang.org/x/sys v0.14.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20231106174013-bbf56f31fb17 // indirect
)

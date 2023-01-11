package server

import (
    "context"
    "log"
    "time"

    "github.com/Jille/raft-grpc-leader-rpc/rafterrors"
    "github.com/golang/protobuf/proto"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
)


type RpcInterface struct {
    Executor *executorFSM
    Raft     *raft.Raft
    pb.UnimplementedJinaSingleDataRequestRPCServer
    pb.UnimplementedJinaDiscoverEndpointsRPCServer
    pb.UnimplementedJinaInfoRPCServer
}


/**
 * jina gRPC func for DataRequests.
 * This is used to send requests to Executors when a list of requests is not needed
 */
func (rpc RpcInterface) ProcessSingleData(
    ctx context.Context,
    dataRequestProto *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    log.Printf("ProcessSingleData")
    endpoint := dataRequestProto.Header.ExecEndpoint
    found := false

    // Loop through the list and check if the search string is in the list
    for _, s := range rpc.Executor.write_endpoints {
        if s == *endpoint {
            found = true
            break
        }
    }

    if found {
        log.Printf("Calling a Write Endpoint")
        log.Printf("rpc method process single data to endpoint %s", *endpoint)
        bytes, err := proto.Marshal(dataRequestProto)
        if err != nil {
            log.Fatal("marshaling error: ", err)
            return nil, err
        }
        // replicate logs to the followers and then to itself
        log.Printf("calling raft.Apply")
        // here we should read the `on=` from dat
        future := rpc.Raft.Apply(bytes, time.Second)
        if err := future.Error(); err != nil {
            return nil, rafterrors.MarkRetriable(err)
        }
        response, test := future.Response().(*pb.DataRequestProto)
        if test {
            log.Printf("Apply FSM returns %s: ", response.String())
            return response, nil
        } else {
            err := future.Response().(error)
            return nil, err
        }
    } else {
        log.Printf("Calling a Read Endpoint")
        return rpc.Executor.Read(ctx, dataRequestProto)
    }
}

func (rpc RpcInterface) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    log.Printf("EndpointDiscovery")
    return rpc.Executor.EndpointDiscovery(ctx, empty)
}

func (rpc RpcInterface) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
    log.Printf("XStatus")
   return rpc.Executor.XStatus(ctx, empty)
}

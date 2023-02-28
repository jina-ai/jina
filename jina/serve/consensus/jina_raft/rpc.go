package server

import (
    "context"
    "log"
    "time"
    "sync/atomic"
    "errors"

    "github.com/Jille/raft-grpc-leader-rpc/rafterrors"
    "github.com/golang/protobuf/proto"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
)

type RpcInterface struct {
    Executor *executorFSM
    Raft     *raft.Raft
    pb.UnimplementedJinaSingleDataRequestRPCServer
    pb.UnimplementedJinaDiscoverEndpointsRPCServer
    pb.UnimplementedJinaInfoRPCServer
}


func (rpc *RpcInterface) getRaftState() raft.RaftState {
    stateAddr := (uint32)(rpc.Raft.State())
    return raft.RaftState(atomic.LoadUint32(&stateAddr))
}

/**
 * jina gRPC func for DataRequests.
 * This is used to send requests to Executors when a list of requests is not needed
 */
func (rpc *RpcInterface) ProcessSingleData(
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
        if rpc.getRaftState() == raft.Leader && rpc.Executor.isSnapshotInProgress() {
            err := errors.New("Leader cannot process write request while Snapshotting")
            log.Print("Error: %v", err)
            return nil, err
        }
        bytes, err := proto.Marshal(dataRequestProto)
        if err != nil {
            log.Print("marshaling error: ", err)
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

func (rpc *RpcInterface) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    log.Printf("EndpointDiscovery")
    return rpc.Executor.EndpointDiscovery(ctx, empty)
}

func (rpc *RpcInterface) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
    log.Printf("XStatus")
   return rpc.Executor.XStatus(ctx, empty)
}

func (rpc *RpcInterface) Check(ctx context.Context, req *healthpb.HealthCheckRequest) (*healthpb.HealthCheckResponse, error) {
    log.Printf("Check")
    return rpc.Executor.Check(ctx, req)
}

func (rpc *RpcInterface) Watch(req *healthpb.HealthCheckRequest, stream healthpb.Health_WatchServer) error {
    healthCheckStatus := &healthpb.HealthCheckResponse{}
    healthCheckStatus.Status = 1
    err := stream.Send(healthCheckStatus)
    if err != nil {
        return err
    }
    return nil
}

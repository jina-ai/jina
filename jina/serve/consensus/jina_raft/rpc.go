package server

import (
    "context"
    "time"
    "sync/atomic"
    "errors"

    "github.com/Jille/raft-grpc-leader-rpc/rafterrors"
    "github.com/golang/protobuf/proto"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
    hclog "github.com/hashicorp/go-hclog"
)

type RpcInterface struct {
    Executor *executorFSM
    Raft     *raft.Raft
    Logger   hclog.Logger
    pb.UnimplementedJinaSingleDataRequestRPCServer
    pb.UnimplementedJinaDiscoverEndpointsRPCServer
    pb.UnimplementedJinaInfoRPCServer
    pb.UnimplementedJinaRPCServer
}


func (rpc *RpcInterface) getRaftState() raft.RaftState {
    stateAddr := (uint32)(rpc.Raft.State())
    return raft.RaftState(atomic.LoadUint32(&stateAddr))
}


func (rpc *RpcInterface) Call(stream pb.JinaRPC_CallServer) error {
  for {
    req, err := stream.Recv()
    if err != nil {
      rpc.Logger.Error("Error receiving request in streaming", "error", err)
      return err
    }
    rpc.Logger.Debug("Received request in streaming")
    // process the input message and generate the response message
    resp, err := rpc.ProcessSingleData(nil, req)
    if err != nil {
        rpc.Logger.Error("Error processing single data", "error", err)
        return err
    }
    // send the response message back to the client
    if err := stream.Send(resp); err != nil {
      rpc.Logger.Error("Error streaming response back", "error", err)
      return err
    }
  }
}


/**
 * jina gRPC func for DataRequests.
 * This is used to send requests to Executors when a list of requests is not needed
 */
func (rpc *RpcInterface) ProcessSingleData(
    ctx context.Context,
    dataRequestProto *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    rpc.Logger.Debug("Calling ProcessSingleData")
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
        rpc.Logger.Debug("Calling a Write Endpoint:", "endpoint", *endpoint)
        if rpc.getRaftState() == raft.Leader && rpc.Executor.isSnapshotInProgress() {
            err := errors.New("Leader cannot process write request while Snapshotting")
            rpc.Logger.Error("Leader cannot process write request while Snapshotting")
            return nil, err
        }
        bytes, err := proto.Marshal(dataRequestProto)
        if err != nil {
            rpc.Logger.Error("Error marshalling DataRequestProto into bytes:", "error", err)
            return nil, err
        }
        // replicate logs to the followers and then to itself
        rpc.Logger.Debug("Call raft.Apply")
        // here we should read the `on=` from dat
        future := rpc.Raft.Apply(bytes, time.Second)
        if err := future.Error(); err != nil {
            rpc.Logger.Error("Error from calling RAFT apply:", "error", err)
            return nil, rafterrors.MarkRetriable(err)
        }
        response, test := future.Response().(*pb.DataRequestProto)
        if test {
            rpc.Logger.Debug("Return from RAFT Apply:", "Response", response.String())
            return response, nil
        } else {
            err := future.Response().(error)
            return nil, err
        }
    } else {
        rpc.Logger.Debug("Calling a Read Endpoint:", "endpoint", *endpoint)
        return rpc.Executor.Read(ctx, dataRequestProto)
    }
}

func (rpc *RpcInterface) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    rpc.Logger.Debug("Get an Endpoint Discovery Request")
    return rpc.Executor.EndpointDiscovery(ctx, empty)
}

func (rpc *RpcInterface) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
   rpc.Logger.Debug("Get an XStatus Request")
   return rpc.Executor.XStatus(ctx, empty)
}

func (rpc *RpcInterface) Check(ctx context.Context, req *healthpb.HealthCheckRequest) (*healthpb.HealthCheckResponse, error) {
    rpc.Logger.Debug("Get a Check Request")
    return rpc.Executor.Check(ctx, req)
}

func (rpc *RpcInterface) Watch(req *healthpb.HealthCheckRequest, stream healthpb.Health_WatchServer) error {
    rpc.Logger.Debug("Get a Watch Request")
    healthCheckStatus := &healthpb.HealthCheckResponse{}
    healthCheckStatus.Status = 1
    err := stream.Send(healthCheckStatus)
    if err != nil {
        rpc.Logger.Error("Error sending back health Check Status", "error", err)
        return err
    }
    return nil
}

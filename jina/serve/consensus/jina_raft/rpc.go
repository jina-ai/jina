package server

import (
    "context"
    "time"
    "sync/atomic"
    "errors"
    "io"

    "github.com/Jille/raft-grpc-leader-rpc/rafterrors"
    "github.com/golang/protobuf/proto"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
    hclog "github.com/hashicorp/go-hclog"
)

type ConsistencyMode string

const (
	Strong   ConsistencyMode = "Strong"
	Eventual ConsistencyMode = "Eventual"
)

// TODO(niebayes): rewrite RpcInterface to Peer which acts as the coordinator between the executor and the raft node.
type RpcInterface struct {
    Executor *executorFSM
    Raft     *raft.Raft
    ConsistencyMode ConsistencyMode
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
  ctx := context.Background()
  for {
    req, err := stream.Recv()
    if err == io.EOF {
      rpc.Logger.Debug("Streaming received", "EOF", err)
      return nil
    }
    if err != nil {
      rpc.Logger.Error("Error receiving request in streaming", "error", err)
      return err
    }
    rpc.Logger.Debug("Received request in streaming")
    // process the input message and generate the response message
    resp, err := rpc.ProcessSingleData(ctx, req)
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

func (rpc *RpcInterface) proposeRequestToRaft(request *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    bytes, err := proto.Marshal(request)
    if err != nil {
        rpc.Logger.Error("Error marshalling DataRequestProto into bytes:", "error", err)
        return nil, err
    }

    rpc.Logger.Debug("Call raft.Apply to propose the request to the RAFT cluster")
    future := rpc.Raft.Apply(bytes, time.Second)
    if err := future.Error(); err != nil {
        rpc.Logger.Error("Error from calling RAFT apply:", "error", err)
        return nil, rafterrors.MarkRetriable(err)
    }

    response, test := future.Response().(*pb.DataRequestProto)
    rpc.Logger.Debug("Got the response from the RAFT cluster")

    if test {
        return response, nil
    } else {
        err := future.Response().(error)
        return nil, err
    }
}

func (rpc *RpcInterface) applyRequestToExecutor(request *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    rpc.Logger.Debug("Invoke the ProcessSingleData RPC on the Executor")

    executor := rpc.Executor.executor
    conn, err := executor.newConnection()
    if err != nil {
        return nil, err
    }
    defer conn.Close()

    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    response, err := client.ProcessSingleData(context.Background(), request)
    if err != nil {
        rpc.Logger.Error("Error when calling Executor", "error", err)
        return nil, err
    }

    return response, nil
}

func (rpc *RpcInterface) handleReadRequest(request *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    rpc.Logger.Debug("Calling a Read Endpoint:", "endpoint", *request.Header.ExecEndpoint)

    if rpc.ConsistencyMode == Eventual {
        // simply forward the request to the executor if the consistency mode is eventual.
        return rpc.applyRequestToExecutor(request)
    }

    // currently, all read requests go to the RAFT cluster for strong consistency.
    // TODO(niebayes): implement read index optimization to reduce the overhead of the RAFT cluster.
    return rpc.proposeRequestToRaft(request)
}

func (rpc *RpcInterface) handleWriteRequest(request *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    rpc.Logger.Debug("Calling a Write Endpoint:", "endpoint", *request.Header.ExecEndpoint)
    if rpc.getRaftState() == raft.Leader && rpc.Executor.isSnapshotInProgress() {
        err := errors.New("leader cannot process write request while snapshotting")
        rpc.Logger.Error("Leader cannot process write request while Snapshotting")
        return nil, err
    }

    // all write requests go to the RAFT cluster.
    return rpc.proposeRequestToRaft(request)
}

/**
 * jina gRPC func for DataRequests.
 * This is used to send requests to Executors when a list of requests is not needed
 */
func (rpc *RpcInterface) ProcessSingleData(
    ctx context.Context,
    request *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    rpc.Logger.Debug("Calling ProcessSingleData")

    endpoint := request.Header.ExecEndpoint

    // true if found the endpoint in the list of read or write endpoints.
    found := false
    isRead := false

    for _, s := range rpc.Executor.read_endpoints {
        if s == *endpoint {
            found = true
            isRead = true
            break
        }
    }

    for _, s := range rpc.Executor.write_endpoints {
        if s == *endpoint {
            found = true
            break
        }
    }

    if !found {
        rpc.Logger.Error("Calling a RAFT-irrelevant Endpoint:", "endpoint", *endpoint)
        return nil, errors.New("calling a raft-irrelevant Endpoint")
    }

    if isRead {
        return rpc.handleReadRequest(request)
    } else {
        return rpc.handleWriteRequest(request)
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

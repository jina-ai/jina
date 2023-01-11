package server

import (
    "context"
    "fmt"
    "io"
    "log"
    "sync"
    "time"

    "google.golang.org/protobuf/proto"
    "google.golang.org/protobuf/types/known/emptypb"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
)


type executorFSM struct {
    executor *executor
    mtx      sync.RWMutex
    snapshot *snapshot
    write_endpoints  []string
}


func NewExecutorFSM(target string) *executorFSM {
    executor := &executor{
                target:             target,
                connection_options: defaultExecutorDialOptions(),
            }

    conn, _ := executor.newConnection()
    defer conn.Close()
    client := pb.NewJinaDiscoverEndpointsRPCClient(conn)
    response, _ := client.EndpointDiscovery(context.Background(), &emptypb.Empty{})
    write_endpoints := response.WriteEndpoints
    return &executorFSM{
        executor: executor,
        write_endpoints: write_endpoints,
    }
}

func (executor *executorFSM) isSnapshotInProgress() bool {
    if executor.snapshot != nil &&
        *executor.snapshot.status == pb.SnapshotStatusProto_RUNNING {
        return true
    }
    return false
}

// triggered once the followers have committed the log
func (fsm *executorFSM) Apply(l *raft.Log) interface{} {
    log.Printf("executorFSM method Apply")
    fsm.mtx.Lock()
    defer fsm.mtx.Unlock()
    for {
        if !fsm.isSnapshotInProgress() {
            // we need not to return error but make it slow, wait until not anymore in progress
            break
        }
        log.Printf("cannot execute Apply because a snapshot is in progress")
        time.Sleep(1 * time.Second)
    }
    if fsm.isSnapshotInProgress() {
        // we need not to return error but make it slow, wait until not anymore in progress
        log.Printf("cannot execute Apply because a snapshot is in progress")
        return fmt.Errorf("Cannot accept new requests when snap shotting is in progress.")
    }
    log.Printf("calling underlying executor")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return err
    }
    defer conn.Close()
    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    dataRequestProto := &pb.DataRequestProto{}
    err = proto.Unmarshal(l.Data, dataRequestProto)
    if err != nil {
        log.Fatal("unmarshaling error: ", err)
        return err
    }

    response, err := client.ProcessSingleData(context.Background(), dataRequestProto)
    if err != nil {
        log.Fatalf("error calling executor: %v", err)
        return err
    }

    return response
}

func (fsm *executorFSM) Snapshot() (raft.FSMSnapshot, error) {
    // Make sure that any future calls to f.Apply() don't change the snapshot.
    log.Printf("executorFSM method Snapshot")
    fsm.mtx.Lock()
    defer fsm.mtx.Unlock()
    log.Printf("calling underlying executor")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaExecutorSnapshotClient(conn)
    response, err := client.Snapshot(context.Background(), &emptypb.Empty{})
    if err != nil {
        log.Fatalf("Error triggering a snapshot: %v", err)
        return nil, err
    }

    snapshot := &snapshot{
        executor:          fsm.executor,
        id:                response.Id,
        status:            &response.Status,
        snapshotDirectory: &response.SnapshotDirectory,
    }
    fsm.snapshot = snapshot

    return snapshot, nil
}

func (fsm *executorFSM) Restore(r io.ReadCloser) error {
    // I think restore here is not well set
    log.Printf("executorFSM method Restore")
    bytes, err := io.ReadAll(r)
    if err != nil {
        return err
    }
    log.Printf("calling underlying executor")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return err
    }
    defer conn.Close()
    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    dataRequestProto := &pb.DataRequestProto{}
    err = proto.Unmarshal(bytes, dataRequestProto)
    if err != nil {
        log.Fatal("unmarshaling error: ", err)
        return err
    }

    _, err = client.ProcessSingleData(context.Background(), dataRequestProto)

    return err
}

func (fsm *executorFSM) Read(ctx context.Context, dataRequestProto *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    log.Printf("executorFSM call Read endpoint")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    response, err := client.ProcessSingleData(ctx, dataRequestProto)
    if err != nil {
        log.Fatalf("Error calling read endpoint: %v", err)
        return nil, err
    }

    return response, err
}

func (fsm *executorFSM) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    log.Printf("executorFSM call EndpointDiscovery")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaDiscoverEndpointsRPCClient(conn)
    response, err := client.EndpointDiscovery(ctx, empty)
    if err != nil {
        log.Fatalf("Error calling EndpointDiscovery endpoint: %v", err)
        return nil, err
    }

    return response, err
}


func (fsm *executorFSM) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
    log.Printf("executorFSM call Status")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaInfoRPCClient(conn)
    response, err := client.XStatus(ctx, empty)
    if err != nil {
        log.Fatalf("Error calling Status endpoint: %v", err)
        return nil, err
    }

    return response, err
}


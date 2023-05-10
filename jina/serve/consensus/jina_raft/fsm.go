package server

import (
    "context"
    "fmt"
    "os"
    "io"
    "io/ioutil"
    "log"
    "sync"
    "time"
    "errors"

    "google.golang.org/protobuf/proto"
    "google.golang.org/protobuf/types/known/emptypb"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
    empty "github.com/golang/protobuf/ptypes/empty"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
    hclog "github.com/hashicorp/go-hclog"
)


type executorFSM struct {
    executor *executor
    mtx      sync.RWMutex
    snapshot *snapshot
    write_endpoints []string
    RaftID   string
    logger   hclog.Logger
}


func NewExecutorFSM(target string, LogLevel string, raftID string) *executorFSM {
    fsm_logger := hclog.New(&hclog.LoggerOptions{
                    Name:   "executorFSM-" + raftID,
                    Level:  hclog.LevelFromString(LogLevel),
                })
    executor := &executor{
                target:             target,
                connection_options: defaultExecutorDialOptions(),
                Logger: fsm_logger,
                }

    conn, _ := executor.newConnection()
    defer conn.Close()
    client := pb.NewJinaDiscoverEndpointsRPCClient(conn)
    response, err := client.EndpointDiscovery(context.Background(), &emptypb.Empty{})
    if err != nil {
        fsm_logger.Error("Error getting endpoints discovery", "error", err)
    }
    write_endpoints := response.WriteEndpoints
    fsm_logger.Debug("List of endpoints that should trigger Raft Apply:", "endpoints", write_endpoints)
    return &executorFSM{
        executor: executor,
        write_endpoints: write_endpoints,
        logger: fsm_logger,
        RaftID: raftID,
    }
}


func DummyExecutorFSM() *executorFSM {
    fsm_logger := hclog.New(&hclog.LoggerOptions{
                    Name:   "executorFSM-dummy",
                    Level:  hclog.LevelFromString("INFO"),
                })
    executor := &executor{
                target:             "0.0.0.0:54321", //TODO: randomize
                connection_options: defaultExecutorDialOptions(),
                Logger: fsm_logger,
            }

    return &executorFSM{
        executor: executor,
        write_endpoints: []string{},
        logger: fsm_logger,
        RaftID: "dummy",

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
    fsm.mtx.Lock()
    defer fsm.mtx.Unlock()
    fsm.logger.Debug("Apply new log entry")
    for {
        if !fsm.isSnapshotInProgress() {
            // we need not to return error but make it slow, wait until not anymore in progress
            break
        }
        fsm.logger.Error("cannot execute Apply because a snapshot is in progress")
        time.Sleep(1 * time.Second)
    }
    if fsm.isSnapshotInProgress() {
        // we need not to return error but make it slow, wait until not anymore in progress
        fsm.logger.Error("Cannot accept new requests when snap shotting is in progress.")
        return fmt.Errorf("Cannot accept new requests when snap shotting is in progress.")
    }
    conn, err := fsm.executor.newConnection()
    if err != nil {
        return err
    }
    defer conn.Close()
    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    dataRequestProto := &pb.DataRequestProto{}
    err = proto.Unmarshal(l.Data, dataRequestProto)
    if err != nil {
        fsm.logger.Error("Error while unmarshalling log into DataRequestProto", "error", err)
        return err
    }

    response, err := client.ProcessSingleData(context.Background(), dataRequestProto)
    if err != nil {
        fsm.logger.Error("Error when calling Executor", "error", err)
        return err
    }
    fsm.logger.Debug("Return Apply Log Response")
    return response
}

func (fsm *executorFSM) Snapshot() (raft.FSMSnapshot, error) {
    // Make sure that any future calls to f.Apply() don't change the snapshot.
    fsm.mtx.Lock()
    defer fsm.mtx.Unlock()
    fsm.logger.Debug("Snapshot FSM state")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaExecutorSnapshotClient(conn)
    response, err := client.Snapshot(context.Background(), &emptypb.Empty{})
    if err != nil {
        fsm.logger.Error("Error triggering a snapshot", "error", err)
        return nil, err
    }
    snapshot := &snapshot{
        executor:          fsm.executor,
        id:                response.Id,
        status:            &response.Status,
        snapshotFile:      response.SnapshotFile,
        Logger:            fsm.logger,
    }
    fsm.snapshot = snapshot
    fsm.logger.Debug("Snapshot successfully attached to FSM")
    return snapshot, nil
}

func (fsm *executorFSM) Restore(r io.ReadCloser) error {
    // I think restore here is not well set
    fsm.logger.Debug("Restore FSM state")
    bytes, err := io.ReadAll(r)
    // write bytes to temporary file, and pass it in the request
    if err != nil {
        fsm.logger.Error("Error reading bytes from the snapshot file", "error", err)
        return err
    }
    tempDir := os.TempDir()
    file, err := ioutil.TempFile(tempDir, "temp")
    if err != nil {
        log.Print(err)
    }
    defer os.Remove(file.Name()) // remove the file when done

     fsm.logger.Debug("Temporary file name where to write state", "filename", file.Name())

    // Write some data to the file
    if _, err := file.Write(bytes); err != nil {
        fsm.logger.Error("Error writing snapshot bytes to temporary file", "error", err)
        return err
    }

    // Close the file
    if err := file.Close(); err != nil {
        fsm.logger.Error("Error closing file", "error", err)
        return err
    }
    fsm.logger.Debug("Calling Executor to request restore")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return err
    }
    defer conn.Close()
    client := pb.NewJinaExecutorRestoreClient(conn)
    restoreCommandProto := &pb.RestoreSnapshotCommand{}
    restoreCommandProto.SnapshotFile = file.Name()
    restoreResponse, err := client.Restore(context.Background(), restoreCommandProto)
    if err != nil {
        fsm.logger.Error("Restore command to Executor failed", "error", err)
        return err
    }
    fsm.logger.Debug("Start Checking status of Restore")
    ticker := time.NewTicker(1 * time.Second)
    done := make(chan bool)
    defer close(done)
    timeout := time.NewTimer(500 * time.Second)

    go func(funcTicker *time.Ticker) {
        for {
            select {
            case t := <-funcTicker.C:
                fsm.logger.Debug("Checking restore status at", "time", t)
                conn, err = fsm.executor.newConnection()
                if err == nil {
                    defer conn.Close()
                    client := pb.NewJinaExecutorRestoreProgressClient(conn)
                    response, err := client.RestoreStatus(context.Background(), restoreResponse.Id)
                    if err != nil {
                        fsm.logger.Error("Error fetching restore status for", "ID", restoreResponse.Id, "error", err)
                    } else {
                        fsm.logger.Debug("Restore", "status", response.Status, "at time", t)
                        if response.Status == pb.RestoreSnapshotStatusProto_FAILED ||
                            response.Status == pb.RestoreSnapshotStatusProto_SUCCEEDED {
                            if response.Status == pb.RestoreSnapshotStatusProto_FAILED {
                                 err = errors.New("Restoring Executor failed")
                            }
                            timeout.Stop()
                            done <- true
                            return
                        }
                    }
                }
            case <-timeout.C:
                fsm.logger.Error("Timed out waiting for restore status.")
                timeout.Stop()
                done <- true
                return
            }
        }
    }(ticker)
    <-done
    ticker.Stop()
    return err
}

func (fsm *executorFSM) Read(ctx context.Context, dataRequestProto *pb.DataRequestProto) (*pb.DataRequestProto, error) {
    fsm.logger.Debug("Call Read Endpoint")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaSingleDataRequestRPCClient(conn)
    response, err := client.ProcessSingleData(ctx, dataRequestProto)
    if err != nil {
        fsm.logger.Error("Error calling Read endpoint", "error", err)
        return nil, err
    }
    fsm.logger.Debug("Return Read Endpoint Response")
    return response, err
}

func (fsm *executorFSM) EndpointDiscovery(ctx context.Context, empty *empty.Empty) (*pb.EndpointsProto, error) {
    fsm.logger.Debug("Call EndpointDiscovery")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaDiscoverEndpointsRPCClient(conn)
    response, err := client.EndpointDiscovery(ctx, empty)
    if err != nil {
        fsm.logger.Error("Error calling EndpointDiscovery endpoint", "error", err)
        return nil, err
    }
    fsm.logger.Debug("Return EndpointDiscovery Response")
    return response, err
}


func (fsm *executorFSM) XStatus(ctx context.Context, empty *empty.Empty) (*pb.JinaInfoProto, error) {
    fsm.logger.Debug("Call XStatus")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return nil, err
    }
    defer conn.Close()
    client := pb.NewJinaInfoRPCClient(conn)
    response, err := client.XStatus(ctx, empty)
    if err != nil {
        fsm.logger.Error("Error calling Status endpoint", "error", err)
        return nil, err
    }
    fsm.logger.Debug("Return XStatus Response")
    return response, err
}


func (fsm *executorFSM) Check(ctx context.Context, req *healthpb.HealthCheckRequest) (*healthpb.HealthCheckResponse, error) {
    fsm.logger.Debug("Call Check")
    conn, err := fsm.executor.newConnection()
    if err != nil {
        fsm.logger.Error("Error setting a new connection with Executor", "error", err)
        return nil, err
    }
    defer conn.Close()
    resp, err := healthpb.NewHealthClient(conn).Check(ctx, req)
    if err != nil {
        fsm.logger.Error("Error calling Check endpoint", "error", err)
        return nil, err
    }
    fsm.logger.Debug("Return Check Response")
    return resp, err
}


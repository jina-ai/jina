package server

import (
    "context"
    "fmt"
    "sync"
    "time"
    "os"
    "io"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
    hclog "github.com/hashicorp/go-hclog"
)

type snapshot struct {
    executor          *executor
    id                *pb.SnapshotId
    mu                sync.RWMutex
    status            *pb.SnapshotStatusProto_Status
    snapshotFile      string
    Logger            hclog.Logger
}

func (s *snapshot) Release() {
}

func (s *snapshot) store(data *pb.SnapshotStatusProto_Status) {
    s.mu.Lock()
    defer s.mu.Unlock()

    s.status = data
}

func (s *snapshot) get() *pb.SnapshotStatusProto_Status {
    s.mu.RLock()
    defer s.mu.RUnlock()

    return s.status
}

func (s *snapshot) Persist(sink raft.SnapshotSink) error {
    s.Logger.Debug("Start persist operation")
    var err error
    ticker := time.NewTicker(1 * time.Second)
    done := make(chan bool)
    defer close(done)
    timeout := time.NewTimer(500 * time.Second)
    var status *pb.SnapshotStatusProto_Status

    defer func() {
        if err != nil || (status != nil && *status != pb.SnapshotStatusProto_SUCCEEDED) {
            failed_snapshot := pb.SnapshotStatusProto_FAILED
            s.store(&failed_snapshot)
            sink.Cancel()
        } else {
            err = sink.Close()
        }
    }()

    go func(funcTicker *time.Ticker) {
        for {
            select {
            case t := <-funcTicker.C:
                s.Logger.Debug("Checking snapshot status at", "time", t)
                conn, err := s.executor.newConnection()
                if err == nil {
                    defer conn.Close()
                    client := pb.NewJinaExecutorSnapshotProgressClient(conn)
                    response, err := client.SnapshotStatus(context.Background(), s.id)
                    if err != nil {
                        s.Logger.Error("Error fetching snapshot status for", "ID", response.Id, "error", err)
                    } else {
                        s.store(&response.Status)
                        s.Logger.Debug("Snapshot", "status", response.Status, "at time", t)
                        if response.Status == pb.SnapshotStatusProto_FAILED ||
                            response.Status == pb.SnapshotStatusProto_SUCCEEDED {
                            timeout.Stop()
                            done <- true
                            return
                        }
                    }
                }
            case <-timeout.C:
                s.Logger.Error("Timed out waiting for snapshot status.")
                timeout.Stop()
                done <- true
                return
            }
        }
    }(ticker)

    <-done
    ticker.Stop()

    status = s.get()
    if status != nil && *status != pb.SnapshotStatusProto_SUCCEEDED {
        msg := fmt.Sprintf("persist job %s failed with status %s", s.id.Value, status)
        s.Logger.Error(msg)
        err = fmt.Errorf(msg)
        return err
    }
    source, err := os.Open(s.snapshotFile)
    if err != nil {
       s.Logger.Error("Error opening a file where Executor created snapshot", "error", err)
       return err
    }
    defer source.Close()

    _, err = io.Copy(sink, source)
    if err != nil {
       s.Logger.Error("Error copying temporary Executor snapshot", "error", err)
       return err
    }
    err = os.Remove(s.snapshotFile)
    if err != nil {
       s.Logger.Error("Error removing Executor shanpshot File", "error", err)
    }
    return err
}

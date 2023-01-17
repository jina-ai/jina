package server

import (
    "context"
    "fmt"
    "log"
    "sync"
    "time"

    "github.com/hashicorp/raft"
    pb "jraft/jina-go-proto"
)

type snapshot struct {
    executor          *executor
    id                *pb.SnapshotId
    mu                sync.RWMutex
    status            *pb.SnapshotStatusProto_Status
    snapshotDirectory string
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
    log.Printf("Starting persist operation...")
    ticker := time.NewTicker(1 * time.Second)
    done := make(chan bool)
    defer close(done)
    timeout := time.NewTimer(500 * time.Second)

    go func(funcTicker *time.Ticker) {
        for {
            select {
            case t := <-funcTicker.C:
                fmt.Println("Checking snapshot status at ", t)
                conn, err := s.executor.newConnection()
                if err == nil {
                    defer conn.Close()
                    client := pb.NewJinaExecutorSnapshotProgressClient(conn)
                    response, err := client.SnapshotStatus(context.Background(), s.id)
                    if err != nil {
                        log.Printf("error fetching snapshot status for id: %s", s.id)
                    }
                    s.store(&response.Status)
                    log.Printf("snapshot status at time %v is %s", t, response.Status)
                    if response.Status == pb.SnapshotStatusProto_FAILED ||
                        response.Status == pb.SnapshotStatusProto_SUCCEEDED {
                        timeout.Stop()
                        done <- true
                        return
                    }
                }
            case <-timeout.C:
                log.Printf("Timed out waiting for snapshot status.")
                timeout.Stop()
                done <- true
                return
            }
        }
    }(ticker)

    <-done
    ticker.Stop()
    status := s.get()
    if status != nil && *status != pb.SnapshotStatusProto_SUCCEEDED {
        msg := fmt.Sprintf("persist job %s failed with status %s", s.id.Value, status)
        log.Fatalf(msg)
        return fmt.Errorf(msg)
    }
    _, err := sink.Write([]byte(s.snapshotDirectory))
    if err != nil {
        _ = sink.Cancel()
        return fmt.Errorf("sink.Write(): %v", err)
    }

    return sink.Close()
}

package server

import (
    "fmt"
    "github.com/hashicorp/raft"
)

// Jina re-implementation of raft.GetConfiguration. Returns the persisted configuration of the Raft cluster
// without starting a Raft instance or connecting to the cluster. This function
// has identical behavior to Raft.GetConfiguration.
func JinaGetConfiguration(conf *raft.Config, fsm raft.FSM, logs raft.LogStore, stable raft.StableStore,
    snaps raft.SnapshotStore, trans raft.Transport) (raft.Configuration, error) {
    r, err := DummyNewRaft(conf, fsm, logs, stable, snaps, trans)
    if err != nil {
        return raft.Configuration{}, err
    }
    future := r.GetConfiguration()
    if err = future.Error(); err != nil {
        return raft.Configuration{}, err
    }
    return future.Configuration(), nil
}

// Jina Re-implementation of NewRaft so that restoring is not triggered. DummyNewRaft is used to get a dummy new Raft node.
// It takes a configuration, as well as implementations of various interfaces that are required. If we have any
// old state, such as snapshots, logs, peers, etc, all those will ** not ** be restored
// when creating the Raft node.
func DummyNewRaft(conf *raft.Config, fsm raft.FSM, logs raft.LogStore, stable raft.StableStore, snaps raft.SnapshotStore, trans raft.Transport) (*raft.Raft, error) {
    // Validate the configuration.
    if err := raft.ValidateConfig(conf); err != nil {
        return nil, err
    }

    // Read the index of the last log entry.
    lastIndex, err := logs.LastIndex()
    if err != nil {
        return nil, fmt.Errorf("failed to find last log: %v", err)
    }

    // Get the last log entry.
    var lastLog raft.Log
    if lastIndex > 0 {
        if err = logs.GetLog(lastIndex, &lastLog); err != nil {
            return nil, fmt.Errorf("failed to get last log at index %d: %v", lastIndex, err)
        }
    }

    // Create Raft struct.
    r := &raft.Raft{}
    return r, nil
}
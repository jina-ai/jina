package server

import (
    "fmt"
    "os"
    "github.com/hashicorp/raft"
    hclog "github.com/hashicorp/go-hclog"
)

// Jina re-implementation of raft.GetConfiguration. Returns the persisted configuration of the Raft cluster
// without starting a Raft instance or connecting to the cluster. This function
// has identical behavior to Raft.GetConfiguration.
func JinaGetConfiguration(conf *raft.Config, fsm raft.FSM, logs raft.LogStore, stable raft.StableStore,
    snaps raft.SnapshotStore, trans raft.Transport) (raft.Configuration, error) {
    logLevel := os.Getenv("JINA_LOG_LEVEL")
    if logLevel == "" {
        logLevel = "INFO"
    }
    logger := hclog.New(&hclog.LoggerOptions{
                    Name:   "GetConfiguration",
                    Level:  hclog.LevelFromString(logLevel),
                })
    logger.Debug("Getting the configuration from the RAFT node")
    r, err := DummyNewRaft(conf, fsm, logs, stable, snaps, trans)
    if err != nil {
        logger.Error("Error creating a New Dummy Raft", "error", err)
        return raft.Configuration{}, err
    }
    future := r.GetConfiguration()
    if err = future.Error(); err != nil {
        logger.Error("Error getting configuration: returning an empty configuration", "error", err)
        return raft.Configuration{}, err
    }
    logger.Debug("Obtained the configuration from the RAFT node")
    return future.Configuration(), nil
}

// Jina Re-implementation of NewRaft so that restoring is not triggered. DummyNewRaft is used to get a dummy new Raft node.
// It takes a configuration, as well as implementations of various interfaces that are required. If we have any
// old state, such as snapshots, logs, peers, etc, all those will ** not ** be restored
// when creating the Raft node.
func DummyNewRaft(conf *raft.Config, fsm raft.FSM, logs raft.LogStore, stable raft.StableStore, snaps raft.SnapshotStore, trans raft.Transport) (*raft.Raft, error) {
    // Validate the configuration.
    logLevel := os.Getenv("JINA_LOG_LEVEL")
    if logLevel == "" {
        logLevel = "INFO"
    }
    logger := hclog.New(&hclog.LoggerOptions{
                    Name:   "DummyNewRaft",
                    Level:  hclog.LevelFromString(logLevel),
                })

    if err := raft.ValidateConfig(conf); err != nil {
        logger.Error("Error validating the Configuration", "error", err)
        return nil, err
    }

    // Read the index of the last log entry.
    lastIndex, err := logs.LastIndex()
    if err != nil {
        logger.Error("Error getting the last index: %v", err)
        return nil, fmt.Errorf("Error getting the last index", "error", err)
    }

    // Get the last log entry.
    var lastLog raft.Log
    if lastIndex > 0 {
        if err = logs.GetLog(lastIndex, &lastLog); err != nil {
            logger.Error("Error getting the last index", "error", err)
            return nil, fmt.Errorf("Error getting the last log at index %d: %v", lastIndex, err)
        }
    }

    // Create Raft struct.
    r := &raft.Raft{}
    return r, nil
}
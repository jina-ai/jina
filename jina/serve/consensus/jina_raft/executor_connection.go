package server

import (
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc"
    hclog "github.com/hashicorp/go-hclog"
)

func defaultExecutorDialOptions() []grpc.DialOption {
    return []grpc.DialOption{
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithDefaultCallOptions(grpc.WaitForReady(true)),
    }
}

type executor struct {
    target             string
    connection_options []grpc.DialOption
    Logger             hclog.Logger
}

func (executor *executor) newConnection() (*grpc.ClientConn, error) {
    conn, err := grpc.Dial(executor.target, executor.connection_options...)
    if err != nil {
        executor.Logger.Error("Dialing failed", "error", err)
        return nil, err
    }
    return conn, err
}

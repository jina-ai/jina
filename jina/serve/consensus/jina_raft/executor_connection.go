package server

import (
	"log"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc"
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
}

func (executor *executor) newConnection() (*grpc.ClientConn, error) {
	conn, err := grpc.Dial(executor.target, executor.connection_options...)
	if err != nil {
		log.Fatalf("dialing failed: %v", err)
		return nil, err
	}
	return conn, err
}

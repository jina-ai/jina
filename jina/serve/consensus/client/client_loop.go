package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/jina-ai/jina-raft/docarray"
	"github.com/jina-ai/jina-raft/jina-go-proto"
	pb "github.com/jina-ai/jina-raft/jina-go-proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	_ "google.golang.org/grpc/health"
)

// Create a Document
func getDoc(id string) *docarray.DocumentProto {
	return &docarray.DocumentProto{
		Id: uuid.New().String(),
		Content: &docarray.DocumentProto_Text{
			Text: "Hello world. This is a test document with id:" + id,
		},
	}
}

// Create a DocumentArray with 3 Documents
func getDocarray(doc_idx int) *docarray.DocumentArrayProto {
	var docs []*docarray.DocumentProto
	docs = append(docs, getDoc(fmt.Sprint(doc_idx)))
	return &docarray.DocumentArrayProto{
		Docs: docs,
	}
}

// Create DataRequest with a DocumentArray
func getDataRequest(doc_idx int) *jina.DataRequestProto {
	execEndpoint := "/index"
	return &jina.DataRequestProto{
		Header: &pb.HeaderProto{
			ExecEndpoint: &execEndpoint,
		},
		Data: &jina.DataRequestProto_DataContentProto{
			Documents: &jina.DataRequestProto_DataContentProto_Docs{
				Docs: getDocarray(doc_idx),
			},
		},
	}
}

var (
	target = flag.String("target", "localhost:50051", "raft node")
)

func main() {
	flag.Parse()

	dialOptions := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	}

	for i := 1; i < 3600; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    	defer cancel()

    	log.Printf("creating dial context for target: %s \n", *target)
    	conn, err := grpc.DialContext(ctx, *target, dialOptions...)
    	if err != nil {
    		log.Fatalf("dialing failed: %v", err)
    	}
    	defer conn.Close()
        client := pb.NewJinaSingleDataRequestRPCClient(conn)
        log.Printf("Executing data request: %i ... \n", i)
        response, err := client.ProcessSingleData(ctx, getDataRequest(i))
        if err != nil {
            log.Fatalf("request failed: %v \n", err)
        } else {
            log.Printf("Received response: %v \n", response)
        }
        time.Sleep(1 * time.Second)
    }
}

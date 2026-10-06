package services

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"google.golang.org/grpc"
)

func UnaryClientInterceptor(ctx context.Context, method string, req, reply interface{}, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) (err error) {
	start := time.Now()
	defer func() {
		in, _ := json.Marshal(req)
		out, _ := json.Marshal(reply)
		inStr, outStr := string(in), string(out)
		duration := int64(time.Since(start).Microseconds())

		delimiter := ";"
		errStr := fmt.Sprintf("%v", err)
		if err == nil {
			errStr = "<nil>"
		}
		logMessage := fmt.Sprintf("grpc%s%s%s%s%s%s%s%s%s%s%s%d", delimiter, method, delimiter, inStr, delimiter, outStr, delimiter, errStr, delimiter, start, delimiter, duration)
		log.Println(logMessage)

	}()

	return invoker(ctx, method, req, reply, cc, opts...)
}

// dial creates a new gRPC client connection to the specified address and returns a client connection object.
func dial(addr string) *grpc.ClientConn {
	// Define gRPC dial options for the client connection.
	opts := []grpc.DialOption{
		grpc.WithInsecure(),
		grpc.WithUnaryInterceptor(UnaryClientInterceptor),
	}

	// Create a new gRPC client connection to the specified address using the dial options.
	conn, err := grpc.Dial(addr, opts...)
	if err != nil {
		// If there was an error creating the client connection, panic with an error message.
		panic(fmt.Sprintf("ERROR: dial error: %v", err))
	}

	// Return the created client connection object.
	return conn
}

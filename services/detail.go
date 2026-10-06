package services

import (
	"context"
	"fmt"
	"log"
	"net"
	"sync"

	"cse190-welp/proto/detail"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Details about one restaurant
type RestaurantDetails struct {
	restaurantName string
	location       string
	style          string
	capacity       int32
}

// Detail implements the detail service
type Detail struct {
	name string
	port int
	detail.DetailServiceServer
	lock sync.Mutex

	dataStore map[string]RestaurantDetails
}

// NewDetail returns a new server for the detail service.
func NewDetail(name string, detailPort int) *Detail {
	return &Detail{
		name:      name,
		port:      detailPort,
		dataStore: make(map[string]RestaurantDetails),
	}
}

// Run starts the Detail gRPC server and listens for incoming requests.
// It returns an error if the server fails to start or encounters an error.
func (s *Detail) Run() error {
	// Create a new gRPC server instance.
	srv := grpc.NewServer()

	// Register the Detail server implementation with the gRPC server.
	detail.RegisterDetailServiceServer(srv, s)

	// Create a TCP listener that listens for incoming requests on the specified port.
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", s.port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// (Optional) Log a message indicating that the server is running and listening on the specified port.
	log.Printf("detail server running at port: %d", s.port)

	// Start serving incoming requests using the registered implementation.
	return srv.Serve(lis)
}

// GetDetail retrieves the details of a restaurant.
// It returns an error if the requested restaurant does not exist.
func (s *Detail) GetDetail(ctx context.Context, req *detail.GetDetailRequest) (*detail.GetDetailResponse, error) {
	s.lock.Lock()
	defer s.lock.Unlock()

	// Get the name of the requested restaurant
	restaurantName := req.GetRestaurantName()
	detailResponse := &detail.GetDetailResponse{}

	var err error

	// Check if the details are stored in the map.
	if details, found := s.dataStore[restaurantName]; found {
		// Found details, copy them to a response message.
		detailResponse = &detail.GetDetailResponse{
			RestaurantName: details.restaurantName,
			Location:       details.location,
			Style:          details.style,
			Capacity:       details.capacity,
		}

		err = status.Errorf(codes.OK, "Found value with Key: %s", restaurantName)
	} else {
		err = status.Errorf(codes.NotFound, "Item with Key: %s does not exist", restaurantName)
	}

	// Return the response object and any error.
	return detailResponse, err
}

// PostDetail adds or updates the details of a restaurant.
func (s *Detail) PostDetail(ctx context.Context, req *detail.PostDetailRequest) (*detail.PostDetailResponse, error) {
	s.lock.Lock()
	defer s.lock.Unlock()

	// Extract fields from the request.
	restaurantName := req.GetRestaurantName()

	// Extract fields from the request into a RestaurantDetails object for local storage.
	details := RestaurantDetails{
		restaurantName: restaurantName,
		location:       req.GetLocation(),
		style:          req.GetStyle(),
		capacity:       req.GetCapacity(),
	}

	// Save the details to the dataStore map.
	s.dataStore[restaurantName] = details

	// Initialize a response object.
	detailResponse := &detail.PostDetailResponse{Status: true}

	// Return the response object.
	return detailResponse, nil
}

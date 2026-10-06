// Lab 2 showcase adaptation: retain only the detail workload endpoints.
package services

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"

	"cse190-welp/proto/detail"
)

type Frontend struct {
	port         int
	detailClient detail.DetailServiceClient
}

func NewFrontend(port int, detailAddr string) *Frontend {
	return &Frontend{port: port, detailClient: detail.NewDetailServiceClient(dial(detailAddr))}
}

func (s *Frontend) Run() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/get-detail", s.getDetailHandler)
	mux.HandleFunc("/post-detail", s.postDetailHandler)
	log.Printf("frontend server running at port: %d", s.port)
	return http.ListenAndServe(fmt.Sprintf(":%d", s.port), mux)
}

// getDetailHandler handles requests for retrieving restaurant details.
func (s *Frontend) getDetailHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	restaurant_name := r.URL.Query().Get("restaurant_name")

	if restaurant_name == "" {
		http.Error(w, "Malformed request to `/get-detail` endpoint!", http.StatusBadRequest)
		return
	}

	req := &detail.GetDetailRequest{RestaurantName: restaurant_name}
	reply, err := s.detailClient.GetDetail(ctx, req)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	_ = json.NewEncoder(w).Encode(reply)
}

// postDetailHandler handles requests for posting restaurant details.
func (s *Frontend) postDetailHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	restaurant_name := r.URL.Query().Get("restaurant_name")
	location := r.URL.Query().Get("location")
	style := r.URL.Query().Get("style")
	capacity, err := strconv.Atoi(r.URL.Query().Get("capacity"))

	if restaurant_name == "" || location == "" || style == "" || err != nil {
		http.Error(w, "Malformed request to `/post-detail` endpoint!", http.StatusBadRequest)
		return
	}

	req := &detail.PostDetailRequest{
		RestaurantName: restaurant_name,
		Location:       location,
		Style:          style,
		Capacity:       int32(capacity),
	}
	reply, err := s.detailClient.PostDetail(ctx, req)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	_ = json.NewEncoder(w).Encode(reply)
}

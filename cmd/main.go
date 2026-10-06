// Lab 2 showcase entry point for the frontend and detail services.
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"runtime"

	"cse190-welp/services"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: welp-lab2 {frontend|detail} [flags]")
		os.Exit(2)
	}
	// Preserve the course baseline's one Go execution thread per process.
	runtime.GOMAXPROCS(1)
	flags := flag.NewFlagSet(os.Args[1], flag.ExitOnError)
	port := flags.Int("port", 8080, "service listening port")
	detailAddr := flags.String("detailaddr", "detail:8081", "detail gRPC address")
	if os.Args[1] == "detail" {
		*port = 8081
	}
	flags.Parse(os.Args[2:])
	var server interface{ Run() error }
	switch os.Args[1] {
	case "frontend":
		server = services.NewFrontend(*port, *detailAddr)
	case "detail":
		server = services.NewDetail("detail", *port)
	default:
		log.Fatalf("unknown service: %s", os.Args[1])
	}
	if err := server.Run(); err != nil {
		log.Fatal(err)
	}
}

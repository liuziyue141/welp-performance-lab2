.PHONY: build check clean

build:
	go build -o bin/welp-lab2 ./cmd

check:
	go vet ./...
	python3 -m unittest discover -s tests -v
	bash -n scripts/run_trial.sh

clean:
	rm -f bin/welp-lab2

FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ cmd/
COPY services/ services/
COPY proto/ proto/
RUN CGO_ENABLED=0 go build -trimpath -o /welp-lab2 ./cmd

FROM alpine:3.21
WORKDIR /app
COPY --from=builder /welp-lab2 /app/welp-lab2
USER 65532:65532
ENTRYPOINT ["/app/welp-lab2"]
CMD ["frontend"]

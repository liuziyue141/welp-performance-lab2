"""Convert frontend gRPC interceptor logs from stdin into a CSV file."""
import argparse
import csv
import json
import re
import sys
from datetime import datetime

HEADER = ["date", "time", "rpc", "input", "output", "error", "start", "duration_us"]
PREFIX = re.compile(r"^(\d{4}/\d{1,2}/\d{1,2} \d{2}:\d{2}:\d{2}) grpc;([^;]+);(.*)$")


def parse_line(line):
    match = PREFIX.match(line.rstrip("\n"))
    if not match:
        return None
    timestamp, method, remaining = match.groups()
    decoder = json.JSONDecoder()
    payloads = []
    for _ in range(2):
        _, end = decoder.raw_decode(remaining)
        payloads.append(remaining[:end])
        if remaining[end:end + 1] != ";":
            raise ValueError("Missing delimiter after JSON payload")
        remaining = remaining[end + 1:]
    error, start, duration = remaining.rsplit(";", 2)
    timestamp = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
    return [timestamp.strftime("%Y-%m-%d"), timestamp.strftime("%H:%M:%S"),
            method, *payloads, error, start, int(duration)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="output CSV path")
    args = parser.parse_args()
    count = 0
    with open(args.output, "w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADER)
        for line in sys.stdin:
            row = parse_line(line)
            if row is not None:
                writer.writerow(row)
                count += 1
    if not count:
        parser.error("No gRPC records found; inspect log format and collection")
    print(f"Parsed {count} gRPC records into {args.output}")


if __name__ == "__main__":
    main()

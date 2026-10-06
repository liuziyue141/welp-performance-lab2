"""Populate the detail service with the dataset used by the Lua workload."""
import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://10.96.88.88:8080")
    parser.add_argument("--samples", type=Path, default=Path("samples/detail_samples.csv"))
    args = parser.parse_args()
    count = 0
    with args.samples.open(newline="") as stream:
        for row in csv.DictReader(stream):
            query = urlencode({
                "restaurant_name": row["RestaurantName"],
                "location": row["Location"],
                "style": row["Style"],
                "capacity": row["Capacity"],
            })
            with urlopen(args.url.rstrip("/") + "/post-detail?" + query, timeout=10) as response:
                payload = json.load(response)
                if payload.get("status") is not True:
                    raise RuntimeError(f"Seeding failed for {row['RestaurantName']}")
            count += 1
    print(f"Seeded {count} restaurant records")


if __name__ == "__main__":
    main()

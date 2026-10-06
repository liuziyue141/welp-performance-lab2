"""Synthetic format fixtures only; these are not historical benchmark data."""
import importlib.util
from pathlib import Path
import unittest


def load(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wrk = load("summarize_wrk")
rpc = load("parse_logs")


class WrkParserTests(unittest.TestCase):
    def test_units_and_errors(self):
        output = """  Latency   539.10us 240.79us 1.32ms 84.23%
  Latency Distribution (HdrHistogram - Recorded Latency)
 99.000% 1.32ms
 5853 completed requests in 1.00m, 760.20KB read
 Socket errors: connect 1, read 2, write 3, timeout 4
 Non-2xx or 3xx responses: 5
Completed Requests/sec (Throughput): 97.55
Sent Requests/sec (Load): 117.36
"""
        result = wrk.parse_output(output)
        self.assertAlmostEqual(result["mean_ms"], 0.5391)
        self.assertEqual(result["p99_ms"], 1.32)
        self.assertEqual(result["completed_rps"], 97.55)
        self.assertEqual(result["sent_rps"], 117.36)
        self.assertEqual(result["timeouts"], 4)
        self.assertEqual(result["non_2xx_3xx"], 5)

    def test_seconds_and_minutes(self):
        self.assertEqual(wrk.milliseconds("2.5", "s"), 2500)
        self.assertEqual(wrk.milliseconds("1", "m"), 60000)

    def test_incomplete_output_rejected(self):
        with self.assertRaises(ValueError):
            wrk.parse_output("unable to connect")


class RpcParserTests(unittest.TestCase):
    def test_method_and_embedded_semicolon(self):
        line = ('2025/02/04 03:45:35 grpc;/detail.DetailService/GetDetail;'
                '{"restaurant_name":"A;B"};{"capacity":100};<nil>;'
                '2025-02-04 03:45:35 +0000 UTC m=+1.2;5279\n')
        row = rpc.parse_line(line)
        self.assertEqual(row[2], "/detail.DetailService/GetDetail")
        self.assertEqual(row[3], '{"restaurant_name":"A;B"}')
        self.assertEqual(row[-1], 5279)

    def test_startup_messages_ignored(self):
        self.assertIsNone(rpc.parse_line("2025/02/04 03:45:35 frontend server running at port: 8080"))


if __name__ == "__main__":
    unittest.main()

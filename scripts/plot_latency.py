import sys
import matplotlib.pyplot as plt
import re

# Initialize an empty list to store the latency values
latencies = []

# Parse each line from stdin
for line in sys.stdin:
    # Use regex to extract the latency value
    match = re.search(r'took (\d+) us', line)
    if match:
        # Convert the matched latency value to an integer and append to the list
        latency_ms = int(match.group(1)) / 1000
        # Append the latency value to the list
        latencies.append(latency_ms)
    elif re.search(r';(\d+)$', line):
        # Split the line by semicolons
        parts = line.strip().split(';')
        # The latency value is the last part after the final semicolon
        latency_ms = int(parts[-1]) / 1000
        # Append the latency value to the list
        latencies.append(latency_ms)

# Plot the latency values
plt.figure(figsize=(10, 6))
# The alpha parameter makes the points transparent. Increase it to make points less transparent.
plt.plot(latencies, marker='o', linestyle='', color='b', alpha=0.02)

# Set the title and labels
plt.title('Latency Values in Milliseconds')
plt.xlabel('Request Index')
plt.ylabel('Latency (ms)')

# Show the plot
plt.grid(True)
plt.savefig(sys.argv[1])

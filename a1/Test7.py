# Test7.py - open http connection, read html, close connection

import time
import http.client

N = 215

start = time.time()

for _ in range(N):
    conn = http.client.HTTPConnection("example.com")
    conn.request("GET", "/")
    res = conn.getresponse()
    html = res.read()
    conn.close()

end = time.time()

elapsed = end - start

print(f"Total time for {N:,} http connections + read html + close connection: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1000:.2f} ms")

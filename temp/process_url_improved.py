import requests
import json

url_to_share = "https://docs.mulligan.dev/vGvJdpKgV7NFjB"
response = requests.post("http://localhost:9999/share", json={"url": url_to_share})

print(f"Status code: {response.status_code}")
if response.status_code == 200:
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.text}")
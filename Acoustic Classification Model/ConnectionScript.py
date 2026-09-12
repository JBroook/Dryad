import requests

code = input("Enter connection code: ")
url = f"http://127.0.0.1:8000/api/devices/connect"

body = {
    "code": code,
    "battery" : 87,
    "coordinate": {
        "type": "Point",
        "coordinates": [101.6869, 3.1390]
    }
}

response = requests.post(url, json=body)

print(response.status_code)
print(response.json())
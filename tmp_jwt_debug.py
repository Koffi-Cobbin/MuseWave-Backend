import json
import urllib.request
import urllib.error

url = "https://kofficobbin.pythonanywhere.com/api/users/debug-jwt"
data = json.dumps({
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc2MjU0MTY5LCJpYXQiOjE3NzYyNTA1NjksImp0aSI6IjY2ZGNmY2IyNmNiZjQwMzQ5YzA1NzkxN2E2NGRiNTc0IiwidXNlcl9pZCI6ImY4ZmJlM2IyLWRhNDYtNDA5ZS1hOTVlLWQ0YWEyOGRiODZhMCJ9.AqjuVFNqa8bicgErCk6t1HWg0uMncGUSXDOnBiYKsAE"
})

req = urllib.request.Request(
    url,
    data=data.encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("HTTP", resp.status)
        print(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("ERR", type(e).__name__, str(e))

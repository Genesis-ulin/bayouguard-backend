import requests

url = "https://www.harriscountyfws.org/Gauge/GetGauges"

headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
gauges = response.json()

print("First 10 gauges in Harris County:\n")
for gauge in gauges[:10]:
    print(f"ID: {gauge.get('SiteId')} - Name: {gauge.get('SiteName')}")
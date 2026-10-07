import requests 
url = "https://www.harriscountyfws.org/Gauge/GetGauges" 
response = requests.get(url) 
print("Status:", response.status_code) 
print("Found", len(response.json()), "gauges") 

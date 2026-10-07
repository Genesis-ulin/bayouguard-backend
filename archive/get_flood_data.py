import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&regionId=4&regionId=10&regionId=22&regionId=1&regionId=14&regionId=18&regionId=19&regionId=23&regionId=20&timeSpan=7&dt=1778349600000"

headers = {
    "Referer": "https://www.harriscountyfws.org/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)
print("Status:", response.status_code)

if response.status_code == 200:
    print("Success! Here's the first 500 characters of data:")
    print(response.text[:500])
else:
    print("Failed. Trying alternative URL...")
    
    # Try the simpler endpoint
    url2 = "https://www.harriscountyfws.org/Gauge/GetGaugeList"
    response2 = requests.get(url2, headers=headers)
    print("Alternative URL Status:", response2.status_code)
    
    if response2.status_code == 200:
        data = response2.json()
        print(f"Success! Found {len(data)} gauges")
        print("First gauge:", data[0] if data else "No data")
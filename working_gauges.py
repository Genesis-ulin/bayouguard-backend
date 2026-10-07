import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"

headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

print("First 10 gauges with their IDs:\n")
for site in sites[:10]:
    props = site["properties"]
    site_id = props.get("SiteId", "Unknown")
    
    # The site name isn't in this endpoint, but we have the ID
    # Let's see what other info we can use
    stream = props["StreamData"][0]
    current = stream["CurrentLevel"]
    flood = stream["ChannelInfo"]["FloodLevelIndicator"]
    
    print(f"ID: {site_id} - Current Level: {current} ft - Flood at: {flood} ft")
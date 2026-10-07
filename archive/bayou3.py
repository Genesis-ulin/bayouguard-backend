import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"

headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

print("BayouGuard - Harris County Flood Gauges\n")

for site in sites[:5]:
    props = site["properties"]
    site_name = props.get("SiteName", props.get("Name", props.get("Text", "No name")))
    stream = props["StreamData"][0]
    current = stream["CurrentLevel"]
    flood = stream["ChannelInfo"]["FloodLevelIndicator"]
    gap = flood - current
    
    if gap <= 2:
        print("⚠️ " + site_name + ": " + str(current) + " ft")
    else:
        print("✅ " + site_name + ": " + str(current) + " ft")

print("\nDone!")
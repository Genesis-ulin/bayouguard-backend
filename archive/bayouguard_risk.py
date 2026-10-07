import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"
headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

print("BayouGuard - Flood Risk Assessment\n")
print("ID    | Current | Flood At | Buffer | Risk")
print("-" * 50)

for site in sites[:20]:
    props = site["properties"]
    site_id = props.get("SiteId", 0)
    stream = props["StreamData"][0]
    current = stream["CurrentLevel"]
    flood = stream["ChannelInfo"]["FloodLevelIndicator"]
    buffer = flood - current
    
    # Calculate risk tier
    if buffer <= 0:
        risk = "CRITICAL"
    elif buffer <= 2:
        risk = "HIGH"
    elif buffer <= 5:
        risk = "MEDIUM"
    elif buffer <= 10:
        risk = "LOW"
    else:
        risk = "SAFE"
    
    # Color indicator
    if risk == "CRITICAL":
        marker = "🔴"
    elif risk == "HIGH":
        marker = "🟠"
    elif risk == "MEDIUM":
        marker = "🟡"
    elif risk == "LOW":
        marker = "🟢"
    else:
        marker = "🔵"
    
    print(f"{marker} {site_id} | {current:5.1f} ft | {flood:5.1f} ft | {buffer:5.1f} ft | {risk}")
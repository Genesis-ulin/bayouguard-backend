import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"
headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

print("BayouGuard - Flood Risk Assessment\n")
print("ID    | Current | Flood At | Buffer | Risk")
print("-" * 50)

for site in sites:
    props = site["properties"]
    site_id = props.get("SiteId", 0)
    
    # Skip if no StreamData
    stream_data = props.get("StreamData")
    if not stream_data or len(stream_data) == 0:
        continue
        
    stream = stream_data[0]
    current = stream.get("CurrentLevel", 0)
    
    channel_info = stream.get("ChannelInfo")
    if not channel_info:
        continue
        
    flood = channel_info.get("FloodLevelIndicator", 999)
    
    # Skip if flood level is not set
    if flood == 999 or flood is None:
        continue
        
    buffer = flood - current
    
    # Calculate risk tier
    if buffer <= 0:
        risk = "CRITICAL"
        marker = "🔴"
    elif buffer <= 2:
        risk = "HIGH"
        marker = "🟠"
    elif buffer <= 5:
        risk = "MEDIUM"
        marker = "🟡"
    elif buffer <= 10:
        risk = "LOW"
        marker = "🟢"
    else:
        risk = "SAFE"
        marker = "🔵"
    
    print(f"{marker} {site_id} | {current:5.1f} ft | {flood:5.1f} ft | {buffer:5.1f} ft | {risk}")

print("\n✅ BayouGuard is monitoring these gauges in real-time!")
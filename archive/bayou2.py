import requests 
url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000" 
headers = {"Referer": "https://www.harriscountyfws.org/"} 
response = requests.get(url, headers=headers)
data = response.json()
sites = data.get("features", [])
print("BayouGuard - Harris County Flood Gauges\n")
for site in sites[:5]:
    props = site.get("properties", {})
    site_name = props.get("SiteName", props.get("Name", props.get("Text", "No name")))
    stream = props.get("StreamData", [])
    if not stream:
        continue
    stream = stream[0]
    current = stream.get("CurrentLevel")
    flood = stream.get("ChannelInfo", {}).get("FloodLevelIndicator")
    if current is None or flood is None:
        continue
    gap = flood - current
    if current >= flood:
        print(f"!! {site_name}: {current} ft / Flood at {flood} ft (AT OR ABOVE FLOOD!)")
    else:
        print(f"? {site_name}: {current} ft / Flood at {flood} ft ({gap:.1f} ft to flood)")

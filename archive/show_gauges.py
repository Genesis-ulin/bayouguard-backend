import requests
import json

url = 'https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000'

headers = {
    'Referer': 'https://www.harriscountyfws.org/'
}

print("Starting script...")

response = requests.get(url, headers=headers)
print("Status code:", response.status_code)

data = response.json()
sites = data['features']

print(f'Found {len(sites)} gauges')
print('=' * 50)

for site in sites[:3]:
    props = site['properties']
    site_name = props['Text']
    stream_data = props['StreamData'][0]
    current_level = stream_data['CurrentLevel']
    channel_info = stream_data['ChannelInfo']
    flood_level = channel_info.get('FloodLevelIndicator', 'No flood stage set')
    
    print(f'{site_name}:')
    print(f'  Current Level: {current_level} ft')
    print(f'  Flood at: {flood_level} ft')
    print()

print("Script finished!")
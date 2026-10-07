import requests
import json

url = 'https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&timeSpan=7&dt=1778349600000'
headers = {'Referer': 'https://www.harriscountyfws.org/'}

response = requests.get(url, headers=headers)
data = response.json()

# Print the first gauge's properties completely
first_gauge = data['features'][0]['properties']
print(json.dumps(first_gauge, indent=2))
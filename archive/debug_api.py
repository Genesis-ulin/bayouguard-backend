import requests 
url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&regionId=4&regionId=10&regionId=22&regionId=1&regionId=14&regionId=18&regionId=19&regionId=23&regionId=20&timeSpan=7&dt=1778349600000" 
headers = {"Referer": "https://www.harriscountyfws.org/", "User-Agent": "Mozilla/5.0"} 
response = requests.get(url, headers=headers) 
print("Status:", response.status_code) 
print(response.text[:500]) 

import requests 
url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&timeSpan=7&dt=1778349600000" 
headers = {"Referer": "https://www.harriscountyfws.org/"} 
response = requests.get(url, headers=headers) 
print("Status:", response.status_code) 
data = response.json() 
print("Keys:", list(data.keys())) 
print(data["features"][0]["properties"]) 

import requests

url = "https://www.harriscountyfws.org/Home/GetSiteRecentData?regionId=3&regionId=24&regionId=25&regionId=26&regionId=21&timeSpan=7&dt=1778349600000"

headers = {"Referer": "https://www.harriscountyfws.org/"}

response = requests.get(url, headers=headers)
data = response.json()
sites = data["features"]

# Look at the first gauge and print ALL its field names
first_gauge = sites[0]["properties"]
print("All fields in this gauge:")
for key in first_gauge.keys():
    print("  - " + key)

print("\nLooking for name fields...")
possible_names = ["SiteName", "Name", "Text", "Title", "Description", "Site"]
for name_field in possible_names:
    if name_field in first_gauge:
        print("Found: " + name_field + " = " + str(first_gauge[name_field]))
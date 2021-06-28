#%%
import json

from corityAPIreportwriter import CorityODataBridge
# %%
baseurl = "https://partner-arcadis.services.cority.com"
with open("credentials.json", 'r') as f:
    creds = json.loads(f.read())[baseurl]

CODB = CorityODataBridge(baseurl, creds["odatakey"])

# %%
reports = CODB.get_reports()
values = CODB.get_values("DT_User[499]")
CODB.export_values("exports/DT_User[499]")

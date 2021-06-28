#%%
import json
import urllib3
import time
import datetime

from corityAPImgip import CorityMGIPBridge
# %%
baseurl = "https://partner-arcadis.services.cority.com"
with open("credentials.json", 'r') as f:
    creds = json.loads(f.read())[baseurl]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CMGIP = CorityMGIPBridge(baseurl, creds['user'], creds['pass'])

today = datetime.datetime.now().strftime("%Y.%m.%d")

# %% import data
msg = CMGIP.import_data(["skytestwebsvc,skysvc"],
                        "EmployeeNumber,LoginId",
                        "Demographics.Employee",
                        bypass_br=True)
print("\n".join(msg))
# %% import from csv file
msg = CMGIP.import_csv("testimp.csv",
                       "EmployeeNumber,LoginId",
                       "Demographics.Employee",
                       bypass_br=True)
print("\n".join(msg))
# %% check valid login
CMGIP.validate_login()
# %% get all tables
tables = CMGIP.get_tables()
tablesdict = CMGIP.get_tables("TableName")


def find_tables_by_text(text):
    return [t for t in tables if json.dumps(t).lower().find(text) > -1]


searchtext = "document"
[t["Model"] for t in find_tables_by_text(searchtext)]

tablesdict["DT_Employee"]
# %%
properties = CMGIP.get_properties("Demographics.Employee")
properties['dataDictionary']
properties['availableProperties']
properties['uniqueKeyProperties']
properties['selectedProperties']

# %% export table template
model = "Lookups.Demographics.UOMCategory"
CMGIP.export_properties(f"exports/modelexports/{model}.csv", model)

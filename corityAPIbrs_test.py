#%% import
from corityAPIbrs import CorityAPIBridge, get_GeneralizedReferenceType
#%% create interface
baseurl = "https://partner-arcadis.services.cority.com"

CAPI = CorityAPIBridge(baseurl, "tokens.json", verbose=False)
# %% refresh access token
CAPI.refresh()
# %% test GET one record
usr = CAPI.get_record("user", 160, True)
# %% test GET multiple records with filter
usrs = CAPI.get_records(
    "user", True, {
        "Fields": "loginName, FirstName, LastName, EmailAddress, Employee.Id",
        "Filters": "EmailAddress:@arcadis.com",
        "PageSize": 5,
        "PageIndex": 0,
        "IncludeTotalCount": True,
    })
# %% test POST create employee
CAPI.create_record("employee", {
    "EmployeeNumber": "sky.test",
    "FirstName": "first",
    "LastName": "andlast",
})
#%% test POST create clinic visit
CAPI.create_record(
    "clinicvisit", {
        "Employee": {
            "EmployeeNumber": " sky"
        },
        "TreatmentDate": "10/16/2020",
        "TreatmentTime": "10:10"
    })
#%% test PATCH update employee
CAPI.update_record("employee", 142, {"UDF1": "udf1 update from api"})

#%% test GET document
CAPI.download_document_file(139, False, "./exports/")

#%% test POST create document, working except for preview thumbnail
CAPI.upload_document_file(
    "example.png",
    {
        "documentId": f"testdoc01",
        "description": "test api import document",
        "documentDate": "2021-06-17",
        "documentType": {
            "code": "MISC"
        },
        "linkTo": 0,
        "safetySuite": "true",
        "referenceType": get_GeneralizedReferenceType("safetyFinding"),
        "finding": {
            'id': 507
        },
        # "referenceType": get_GeneralizedReferenceType("generalIncident"),
        # "generalIncident": {'id': 107},
    },
)
# %%

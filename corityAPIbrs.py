import requests
import json
import base64
"""
Accesses the Cority REST API as documented in the Swagger doc.
Main endpoints are:
READ    /entity
READ    /entity?id=0
UPDATE  /entity?id=0
INSERT  /entity
"""
"""
TODO add new features
2021-06-07
    CCC-1033: A RESTful API GET call can now retrieve data within a record
    that is two levels down
        The GET call must query for only one record and must specify the sublist(s).
        o For example, if the current call without requesting sublist data is
        [http://client.cority.com/api/clinicvisit/]<ID>, the new call could be
        [http://client.cority.com/api/clinicvisit/]<ID>?Sublists=vitalsigns,riskassessments&Fields
        =clinicalTests.sampledate,RiskAssessment.RiskAssessmentId.
        • In order for records to be returned, the GET call must specify the desired fields from each
        sublist.
        o For example:
        [http://client.cority.com/api/clinicvisit/]<ID>?Sublists=audiometricTests,riskAssessment
        s,clinicalTests&Fields=Id,TreatmentDate&SublistFields=clinicalTests.sampledate,RiskAss
        essment.RiskAssessmentId.
        • The data that is populated will depend on the user's currently pinned view. The columns in the
        pinned view for the sublist will be populated with the requested, returned data.
        • To request a sublist within a GET call, the sublist must be specified using FormList.Name from
        the FormDto of the parent record. That is the default name of the sublist, with the spaces
        removed.
        o The same identifier must be used in GetOptions (url param) to specify that the sublist
        should be included, and the node must have the same format.
        ▪ For example:
        [http://client.cority.com/api/clinicvisit/|http://client.cority.com/api/clinicvisit/]
        <ID>?Sublists=audiometricTests,riskAssessments,clinicalTests...
    CCC-1052: You can now create a Clinical Test or Drug Test record using the Cority RESTful API and an HL7 file
        The Cority RESTful API has two new post endpoints:
        o ClinicalTestImport
        o DrugTestImport
        • To access the desired endpoint, the user's role has to be granted the corresponding security
        action:
        o ClinicalTestSample.apiwrite
        o DrugTestSample.apiwrite
        • For the import, the following parameters will be accepted in the URL:
        o Clinical Test Standard - required, if not providing a Drug Test standard
        ▪ Labcorp
        ▪ Oxford
        ▪ HL7v23
        ▪ Gamma Dyna Care
        ▪ ASTM88
        ▪ ASTM94
        ▪ HL7v22
        o Drug Test Standard - required, if not providing a Clinical Test standard
        ▪ Quest
        ▪ HL7v23
        ▪ ASTM
        ▪ Labcorp
        ▪ Medtox
        o Laboratory (Look-up Table) - required
        o Health Center (Look-up Table) - required
        o Practitioner (Data Table)
        11
        • Once an HL7 file has been provided to one of the two new endpoints, the following will occur:
        o The data will be delivered to the appropriate service (ClinicalTestImport or
        DrugTestImport).
        o A response with the results of the import (number of records added/updated/rejected)
        will be sent.
        o The results will be logged in the corresponding section (Clinical Test Import View or Drug
        Test Import View) of the Process Status and Log.
        o If the import is successful, the record(s) will be present in the corresponding module
        (Clinical Testing or Drug Testing).
"""

token_file = "tokens.json"
GeneralizedReferenceType_file = "GeneralizedReferenceType.json"
GRT = None


def get_GeneralizedReferenceType(type):
    """ Cache data in file, return case-agnostic values"""
    global GRT
    if GRT is None:
        with open(GeneralizedReferenceType_file, 'r') as f:
            GRT = json.loads(f.read())["data"]
        GRT = {k.lower(): v for k, v in GRT.items()}
    return GRT[type.lower()]


class CorityAPIBridge:
    #def __init__(self, siteurl, refreshtoken=None, verbose=False):
    def __init__(self, siteurl, token_file, verbose=False):
        self.verbose = verbose
        self.SiteUrl = siteurl
        self.token_file = token_file
        self.read_tokens()
        self.refresh()

    def refresh(self, accessonly=False):
        if self.verbose: print("Refreshing...")
        if accessonly:
            response = self.get("Token/Refresh")
            data = response.json()
            self.AccessToken = data["access_token"]
        else:
            response = self.get("Token/Get", {"t": self.RefreshToken})
            data = response.json()
            if 'Message' in data:
                if data['Message'] == "Refresh Token expired":
                    print(data['Message'])
            else:
                self.RefreshToken = data["RefreshToken"]
                self.AccessToken = data["AccessToken"]
                self.AccessTokenExpiry = data["AccessTokenExpiryDateTime"]

        if self.verbose: self.print_tokens()
        self.dump_tokens()

    def print_tokens(self):
        print("My tokens:")
        print("Refresh token: ", self.RefreshToken)
        print("Access token: ", self.AccessToken)
        print("Access token expiry: ", self.AccessTokenExpiry)

    def dump_tokens(self, filename=token_file):
        if self.verbose: print("Dumping tokens to file", filename)
        self.token_data[self.SiteUrl] = {
            "RefreshToken": self.RefreshToken,
            "AccessToken": self.AccessToken,
            "AccessTokenExpiry": self.AccessTokenExpiry,
        }
        with open(filename, "w") as f:
            f.write(json.dumps(self.token_data, indent=4))

    def read_tokens(self, filename=token_file):
        if self.verbose: print("Reading tokens from file", filename)
        data = None
        with open(filename, "r") as f:
            data = json.loads(f.read())
        if len(data) > 0:
            self.token_data = data
            if self.SiteUrl in data:
                self.RefreshToken = data[self.SiteUrl]["RefreshToken"]
                self.AccessToken = data[self.SiteUrl]["AccessToken"]
                self.AccessTokenExpiry = data[
                    self.SiteUrl]["AccessTokenExpiry"]

    def get(self, endpoint, parameters={}, headers={}):
        if self.verbose:
            print("Sending GET request to: "
                  f"{self.SiteUrl}/api/{endpoint}", "with headers", headers,
                  "and parameters", parameters)
        response = requests.get(
            f"{self.SiteUrl}/api/{endpoint}",
            params=parameters,
            headers=headers,
            verify=False,
        )
        if self.verbose:
            print("Response:", response.status_code, response.reason)
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=4))
        return response

    def post(self, endpoint, body={}, headers={}):
        if self.verbose:
            print("Sending POST request to: "
                  f"{self.SiteUrl}/api/{endpoint}", "with body", body,
                  "and headers", headers)
        response = requests.post(
            f"{self.SiteUrl}/api/{endpoint}",
            json=body,
            headers=headers,
            verify=False,
        )
        if self.verbose:
            print("Response:", response.status_code, response.reason)
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=4))
        return response

    def put(self, endpoint, body={}, headers={}):
        if self.verbose:
            print("Sending PUT request to: "
                  f"{self.SiteUrl}/api/{endpoint}", "with body", body,
                  "and headers", headers)
        response = requests.put(
            f"{self.SiteUrl}/api/{endpoint}",
            json=body,
            headers=headers,
            verify=False,
        )
        if self.verbose:
            print("Response:", response.status_code, response.reason)
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=4))
        return response

    def get_auth(self, endpoint, parameters={}):
        headers = {"Authorization": f"Bearer {self.AccessToken}"}
        return self.get(endpoint, parameters=parameters, headers=headers)

    def post_auth(self, endpoint, body={}):
        headers = {"Authorization": f"Bearer {self.AccessToken}"}
        return self.post(endpoint, body=body, headers=headers)

    def put_auth(self, endpoint, body={}):
        headers = {"Authorization": f"Bearer {self.AccessToken}"}
        return self.put(endpoint, body=body, headers=headers)

    def get_records(self, entity, asdata=False, parameters={}):
        if self.verbose: print("Getting records for", entity)
        response = self.get_auth(f"{entity}", parameters)
        if response.status_code == 200 and asdata:
            if 'totalCount' in response.json():
                return response.json()['records'], response.json(
                )['totalCount']
            else:
                return response.json()['records']
        return response

    def get_record(self, entity, id, asdata=False, parameters={}):
        if self.verbose: print("Getting record", entity, id)
        response = self.get_auth(f"{entity}/{id}", parameters)
        if response.status_code == 200 and asdata:
            return response.json()['record']
        return response

    def create_record(self, entity, data, asdata=False):
        # TODO include options for {} and [{},{}]
        if self.verbose: print("Creating record", entity, data)
        response = self.post_auth(entity, body=data)
        if response.status_code == 200 and asdata:
            return response.json()['record']
        return response

    def update_record(self, entity, id, data, asdata=False):
        if self.verbose: print("Updating record", entity, id)
        response = self.put_auth(f"{entity}/{id}", data)
        if response.status_code == 200 and asdata:
            return response.json()['record']
        return response

    def get_record_count(self, entity, filter=""):
        response = self.get_records(
            entity,
            True,
            {
                "Fields": "Id",  # might break if entity doesn't have id
                "Filters": filter,
                "PageSize": 2,
                "PageIndex": 0,
                "IncludeTotalCount": True,
            })
        try:
            return response[1]
        except:
            print("ERROR")
            return response

    def download_document_file(self, id, overwrite=False, path="./"):
        response = self.get_record(
            "document",
            id,
            parameters={'AdditionalFields': "DocumentBlobData"})
        # response = CAPI.get_record(
        #     "document",
        #     id,
        #     parameters={'Fields': "documentId,DocumentBlobData,documentName"})
        blob = response.json()['record']['documentBlobData']
        binary = base64.b64decode(blob)
        o_filename = response.json()['record']['documentName']

        # TODO check if file exists, prompt for overwrite
        if not overwrite and False:
            raise FileExistsError
        with open(path + o_filename, 'wb') as f:
            f.write(binary)

    def upload_document_file(self, filename, record_data):
        with open(filename, 'rb') as f:
            imgdata = f.read()

        bstring = base64.b64encode(imgdata)
        estring = bstring.decode("utf-8")

        record_data["documentName"] = filename
        record_data["documentBlobData"] = estring
        record_data["documentPreview"] = estring  # TODO fix?

        response = self.create_record("document", record_data, True)
        if type(response) == dict:
            print("✓")
        else:
            print(response, response.text)

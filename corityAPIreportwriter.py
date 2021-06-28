import requests


class CorityODataBridge:
    def __init__(self, baseurl: str, apikey: str):
        self.baseurl = baseurl
        self.url = f"{baseurl}/odata/reportwriter"
        self.apikey = apikey
        self.params = {"ApiKeyName": "WebApiKey", "WebApiKey": apikey}
        self.headers = {"accept": "application/json"}
        self.verify = False

    def get_reports(self) -> list:
        response = requests.get(self.url,
                                params=self.params,
                                headers=self.headers,
                                verify=self.verify)
        if response.status_code == 200:
            return [r["name"] for r in response.json()['value']]
        else:
            print(response.status_code, response.reason,
                  "Error getting reports from", self.url)
            return response

    def get_values(self, reportname: str) -> list:
        request_url = self.url + f"/{reportname}"
        response = requests.get(request_url,
                                params=self.params,
                                headers=self.headers,
                                verify=self.verify)
        if response.status_code == 200:
            return [r for r in response.json()['value']]
        else:
            print(response.status_code, response.reason,
                  "Error getting values from", request_url)
            return response

    def export_values(self,
                      reportname: str,
                      filename: str = None,
                      delimiter: str = ",",
                      qualifier: str = '"') -> None:
        values = self.get_values(reportname)
        headers = values[0].keys()
        if filename is None:
            filename = reportname
        if filename[-4:] != ".csv":
            filename += ".csv"
        with open(filename, 'w') as f:
            f.write(
                delimiter.join([qualifier + h + qualifier
                                for h in headers]) + "\n")
            for value in values:
                f.write(
                    delimiter.join([
                        qualifier + str(value[h]) + qualifier for h in headers
                    ]) + "\n")

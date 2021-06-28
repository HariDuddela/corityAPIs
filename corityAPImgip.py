import logging.config
import gzip
import json
import csv
import ast
from requests import Session

from zeep import Client
from zeep.transports import Transport
from zeep.wsse.signature import Signature


class CorityMGIPBridge:
    def __init__(self, siteurl, username=None, password=None):
        self.siteurl = siteurl
        self.username = username
        self.password = password
        self.wsdl = siteurl + "/WebService/MGIPService.svc?wsdl"
        session = Session()
        session.verify = False
        self.client = Client(self.wsdl, transport=Transport(session=session))
        if not self.validate_login():
            raise Exception("Invalid username/password")

    def validate_login(self):
        return self.client.service.ValidateUserLogin(self.username,
                                                     self.password)

    def convert_to_dict(self, data):
        return ast.literal_eval(str(data))

    def get_tables(self, dict_key=None):
        tables = self.client.service.GetTables(self.username, self.password)
        tables = self.convert_to_dict(tables)
        if dict_key and dict_key in tables[0]:
            return {t[dict_key]: t for t in tables}
        else:
            return tables

    def export_tables(self, filename):
        tables = self.get_tables()
        if filename[-4:] == "json":
            with open(filename, 'w') as f:
                f.write(json.dumps(tables, indent=4))
        elif filename[-3:] == "csv":
            with open(filename, 'w', newline="") as f:
                writer = csv.writer(f,
                                    delimiter=",",
                                    quotechar='"',
                                    quoting=csv.QUOTE_ALL)
                headers = tables[0].keys()
                writer.writerow(headers)
                for table_data in tables:
                    values = [table_data[h] for h in headers]
                    writer.writerow(values)
        else:
            raise Exception("Invalid file type, please use .json or .csv")

    def get_properties(self, model):
        properties = self.client.service.GetModelProperties(
            self.username, self.password, model, False, False, False)
        properties = self.convert_to_dict(properties)
        return properties

    def export_properties(self, filename, model):
        if filename[-3:] == "csv":
            # tableinfo = [t for t in tables if t["Model"] == model][0]
            properties = self.get_properties(model)

            # TODO might need fixing

            exp_data = []
            keys = []
            try:
                keys = properties['uniqueKeyProperties']['string']
            except:
                pass
            importfields = properties['availableProperties']['string']

            fields = {
                x['Key']: x['Value']['string']
                for x in properties['dataDictionary'][list(
                    properties["dataDictionary"].keys())[0]]
                if x['Key'].find(".TreeMasterCodeType.") == -1
            }
            for field, fieldinfo in fields.items():
                fieldobj = dict(
                    zip([
                        "Field", "Field Table", "SQL Type", "Size", "Type",
                        "SQL Size", "Field Description"
                    ], fieldinfo))
                fieldobj["Key"] = True if field in keys else False
                fieldobj[
                    "Importable"] = True if field in importfields else False
                exp_data.append(fieldobj)

            headers = [
                'Field',
                'Field Table',
                'SQL Type',
                'Size',
                # 'Type',
                # 'SQL Size',
                'Field Description',
                'Key',
                'Importable',
            ]

            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f,
                                    delimiter=",",
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(headers)
                writer.writerows([[o[h] for h in headers] for o in exp_data])

        else:
            raise Exception("Invalid file type, please use .csv")

    def import_data(self,
                    data,
                    headers,
                    model,
                    update=False,
                    insert_base_table=False,
                    insert_multiple=False,
                    always_insert=False,
                    header_row=False,
                    xml=False,
                    date_format="mm/dd/yyyy",
                    bypass_br=False):
        """
        data should be a list of comma-separated strings
        headers should be a comma-separated string
        """

        data_s = "\n".join(data)
        data_b = bytearray()
        data_b.extend(map(ord, data_s))  # convert to byte array
        data_g = gzip.compress(data_b)  # convert to gzip stream

        response = self.client.service.DoImport(data_g, headers, model,
                                                self.username, self.password,
                                                update, insert_base_table,
                                                insert_multiple, always_insert,
                                                header_row, xml, date_format,
                                                None, None, bypass_br)
        return response.split("\n")

    def import_csv(self,
                   filename,
                   headers,
                   model,
                   update=False,
                   insert_base_table=False,
                   insert_multiple=False,
                   always_insert=False,
                   header_row=False,
                   xml=False,
                   date_format="mm/dd/yyyy",
                   bypass_br=False):
        data = []
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for line in reader:
                data.append(",".join(line))
        return self.import_data(data, headers, model, update,
                                insert_base_table, insert_multiple,
                                always_insert, header_row, xml, date_format,
                                bypass_br)

    def enable_enhanced_logging(self):
        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'verbose': {
                    'format': '%(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'zeep.transports': {
                    'level': 'DEBUG',
                    'propagate': True,
                    'handlers': ['console'],
                },
            }
        })


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return test_f.read(2) == b'\x1f\x8b'

from bs4 import BeautifulSoup
from csv import DictReader
from json import load
from ldap import LDAP_API
from pyairtable import Table
from requests import get
from sys import stderr
from src_row import SrcRow
from time import sleep

THROTTLE_INTERVAL = 0.2

class App():
    def __init__(self):
        private = App._load_private()
        self.table = Table(private["API_KEY"], private["BASE_ID"], private["TABLE_NAME"])
        self._ldap = LDAP_API(private["LDAP_HOST"], private["LDAP_OC"])

    @staticmethod
    def _load_private(pth='./private.json'):
        with open(pth, 'r') as f:
            return load(f)

    def get_by_emplid(self, emplid):
        'Returns the Airtable record for the given employee ID'
        return self.table.first(formula=f'{{University ID}} = "{emplid}"')

    def netid_from_ldap(self, employee_id):
        return self._ldap.query(employee_id, 'universityid')['uid']

    def add_new_record(self, csv_row):
        csv_row = SrcRow(r)
        airtable_record = app.get_by_emplid(csv_row.emplid)
        if airtable_record:
            name = airtable_record['Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            data = App._map_csv_row_to_airtable_fields(csv_row)
            self.table.create(data)
            print(f'Added {csv_row.emplid}')

    def sync_with_csv(self, csv_path):
        # TODO: need to validate sheet
        # TODO: this needs logging (exceptions, updates, adds)

        with open('csv_path, 'r') as f:
            src_data = DictReader(f)
            for r in src_data:
                csv_row = SrcRow(r)
                airtable_record = app.get_by_emplid(csv_row.emplid)
                if airtable_record:
                    data = { } # TODO: needd to decide what fields should by updated
                    app.table.update(airtable_record['id'], data)
                else:
                    app.add_new_record(csv_row)
                    sleep(THROTTLE_INTERVAL)


    @staticmethod
    def get_thumbnail_url(netid):
        try:
            page_url = f'https://library.princeton.edu/staff/{netid}'
            response = get(page_url)
            response.raise_for_status()
            html = BeautifulSoup(response.content, 'html.parser')
            image_url = html.select('div.user--picture')[0].find_all('img')[0]['src'].split('?')[0]

            sleep(THROTTLE_INTERVAL)
            if image_url.endswith('.svg'):
                return None
            else:
                return image_url
        except Exception as e:
            print(str(e), file=stderr)

    @staticmethod
    def _map_csv_row_to_airtable_fields(csv_row):
        try:
            data = {}
            data['University ID'] = csv_row.emplid
            data['Division Code'] = csv_row['Dept']
            data['Division Name'] = csv_row['Department Name']
            data['Admin. Unit'] = csv_row.admin_unit
            data['Search Status'] = 'Hired'
            phone = csv_row.phone
            if phone:
                data['University Phone'] = phone
            data['Term'] = csv_row.term_end
            data['Title'] = csv_row['Position - Job Title']
            data['Email'] = csv_row['E-Mail']
            data['Preferred Name'] = csv_row.preferred_name
            data['Last Name'] = csv_row.last_name
            data['First Name'] = csv_row.first_name
            data['Time'] = csv_row.time
            data['Start Date'] = csv_row.start_date
            data['Grade'] = csv_row.grade
            data['Sal. Plan'] = csv_row['Sal Plan']
            data['Position Number'] = csv_row.position_number
            data['Address'] = csv_row['Telephone DB Office Location']
            netid = app.netid_from_ldap(csv_row.emplid)
            data['netid'] = netid
            thumbnail = App.get_thumbnail_url(netid)
            if thumbnail:
                data['Headshot'] = [ {'url': thumbnail} ]
            return data
        except Exception as e:
            print(f'Error with emplid {csv_row.emplid}', file=stderr)
            raise e

    # TODO: be able to hand this a report and have it decide what fields to
    # update, records to add, and report when an employee is no longer on in the
    # report but still in airtable. Should also be able to validate the report
    # in case the fields have changed

def print_json(json_payload):
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2))

# TODO: a second pass, linking supervisors via emplid, and marking "is supervisor"

if __name__ == '__main__':

    app = App()
    # Load CSV.

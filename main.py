from bs4 import BeautifulSoup
from csv import DictReader
from json import load
from pyairtable import Table
from requests import get
from staff_management.ldap import LDAP_API
from staff_management.src_row import SrcRow
from sys import stderr
from sys import stdout
from time import sleep

THROTTLE_INTERVAL = 0.2

class App():
    def __init__(self, src_data_path):
        private = App._load_private()
        self.table = Table(private["API_KEY"], private["BASE_ID"], private["TABLE_NAME"])
        self._ldap = LDAP_API(private["LDAP_HOST"], private["LDAP_OC"])
        self._src_data = App._load_src_data(src_data_path)

    def get_by_emplid(self, emplid):
        'Returns the Airtable record for the given employee ID'
        return self.table.first(formula=f'{{University ID}} = "{emplid}"')

    def sync_with_csv(self, csv_path):
        # TODO: need to validate sheet
        # TODO: this needs logging (exceptions, updates, adds)
        for r in self._src_data:
            csv_row = SrcRow(r)
            airtable_record = app.get_by_emplid(csv_row.emplid)
            if airtable_record:
                data = { } # TODO: needd to decide what fields should by updated
                app.table.update(airtable_record['id'], data)
            else:
                app._add_new_record(csv_row)
                sleep(THROTTLE_INTERVAL)

    def update_supervisor_hirearchy(self, csv_path):
        for r in self._src_data:
            csv_row = SrcRow(r)
            try:
                employee_at_record = app.get_by_emplid(csv_row.emplid) # TODO: Will error if not found
                supervisor_at_record = app.get_by_emplid(csv_row.super_emplid)
                updates = [{
                    "id" : supervisor_at_record['id'],
                    "fields" : { "Is Supervisor?" : True }
                },{
                    "id" : employee_at_record['id'],
                    "fields" : {
                        "Manager/Supervisor" : [ supervisor_at_record['id'] ]
                    }
                }]
                self.table.batch_update(updates)
                # TODO: could build a big struct at once if we wanted (above), rather than row by row
            except Exception as e:
                print("****Error****", file=stderr)
                print('Employee record:', file=stderr)
                print_json(employee_at_record, f=stderr)
                print('Supervisor record:', file=stderr)
                print_json(supervisor_at_record, f=stderr)
                print(f"Original Error: {str(e)}", file=stderr)
                #TODO likely a missing supervisor. Print name from CSV?
            sleep(THROTTLE_INTERVAL)

    def _netid_from_ldap(self, employee_id):
        return self._ldap.query(employee_id, 'universityid')['uid']

    def _add_new_record(self, csv_row):
        csv_row = SrcRow(r)
        airtable_record = app.get_by_emplid(csv_row.emplid)
        if airtable_record:
            name = airtable_record['Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            data = App._map_csv_row_to_airtable_fields(csv_row)
            self.table.create(data)
            print(f'Added {csv_row.emplid}')

    @staticmethod
    def _load_private(pth='./private.json'):
        with open(pth, 'r') as f:
            return load(f)

    @staticmethod
    def _load_src_data(src_data_path):
        with open(src_data_path, 'rb') as f:
            self._src_data = list(DictReader(f, dialect='excel'))

    @staticmethod
    def _get_thumbnail_url(netid):
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
    def _map_csv_row_to_airtable_fields(csv_row, scrape_photo=False):
        # TODO: What would a better report have?
        # * Long Title
        # * netid
        # Funding source
        try:
            data = {}
            data['University ID'] = csv_row.emplid
            data['Division'] = csv_row['Department Name']
            data['Admin. Unit'] = csv_row.admin_unit
            data['Search Status'] = 'Hired'
            phone = csv_row.phone
            if phone:
                data['University Phone'] = phone
            data['End Date'] = csv_row.term_end
            data['Term/Perm/CA Track'] = csv_row.term_perm
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
            netid = app._netid_from_ldap(csv_row.emplid)
            data['netid'] = netid
            if scrape_photo:
                thumbnail = App._get_thumbnail_url(netid)
                if thumbnail:
                    data['Headshot'] = [ {'url': thumbnail} ]
            return data
        except Exception as e:
            print(f'Error with emplid {csv_row.emplid}', file=stderr)
            raise e

def print_json(json_payload, f=stdout):
    # For debugging
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

if __name__ == '__main__':

    # Choose "Run Excel data!"
    report = './Alpha Roster - Job and Personal Data - Point in Time acd90f65b.xlsx'
    app = App(report)
    for row in app._src_data:
        print(row)
    # app.update_supervisor_hirearchy(report)

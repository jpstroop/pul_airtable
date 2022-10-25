from bs4 import BeautifulSoup
from csv import DictReader
from json import load
from pyairtable import Table
from re import sub
from requests import get
from staff_management.ldap import LDAP_API
from staff_management.src_row import SrcRow
from sys import stderr
from sys import stdout
from time import sleep

THROTTLE_INTERVAL = 0.2

class App():
    VACANT_IMAGE = 'https://dl.airtable.com/.attachments/d5340fc21c451f1733d6ebfff1c79d70/897912fb/Vacant.png'
    def __init__(self, src_data_path):
        private = App._load_private()
        self.table = Table(private["API_KEY"], private["BASE_ID"], private["TABLE_ID"])
        self._ldap = LDAP_API(private["LDAP_HOST"], private["LDAP_OC"])
        self._src_data = App._load_src_data(src_data_path)
        self._next_vacancy_number = None

    def get_airtable_record_by_emplid(self, emplid):
        'Returns the Airtable record for the given employee ID'
        return self.table.first(formula=f'{{University ID}} = "{emplid}"')

    def sync_airtable_with_report(self):
        # TODO: need to validate sheet
        # TODO: this needs logging (exceptions, updates, adds)
        for r in self._src_data:
            csv_row = SrcRow(r)
            airtable_record = app.get_airtable_record_by_emplid(csv_row.emplid)
            if airtable_record:
                data = App._map_csv_row_to_airtable_fields(csv_row, update=True)
                app.table.update(airtable_record['id'], data)
            else:
                app._add_new_record(csv_row)
                sleep(THROTTLE_INTERVAL)

    def update_supervisor_hierarchy(self):
        for r in self._src_data:
            csv_row = SrcRow(r)
            try:
                employee_at_record = app.get_airtable_record_by_emplid(csv_row.emplid) # TODO: Will error if not found
                supervisor_at_record = app.get_airtable_record_by_emplid(csv_row.super_emplid)
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


    def check_all_eplids_from_report_in_airtable(self):
        airtable_emplids = self._all_emplids_from_airtable()
        report_emplids = self._all_emplids_from_report()
        missing_from_airtable = [i for i in report_emplids if i not in airtable_emplids]
        for emplid in missing_from_airtable:
            name = self._get_record_from_report_by_emplid(emplid)["Name"]
            print(f'Employee {emplid} ({name}) is missing from Airtable; #sync_airtable_with_report() will add them.')
        
    def check_all_eplids_from_airtable_in_report(self):
        airtable_emplids = self._all_emplids_from_airtable()
        report_emplids = self._all_emplids_from_report()
        missing_from_report = [i for i in airtable_emplids if i not in report_emplids]
        for emplid in missing_from_report:
            name = self.get_airtable_record_by_emplid(emplid)['fields'].get('Preferred Name')
            if name != "Anne Jarvis":
                print(f'Employee {emplid} ({name}) is missing from CSV Report; #employee_to_vacancy(emplid) will remove them.')

    def employee_to_vacancy(self, emplid):
        airtable_record = self.get_airtable_record_by_emplid(emplid)
        data =  {
            "Address": None,
            "Email": None,
            "First Name": None,
            "Headshot": [ {'url': App.VACANT_IMAGE} ],
            "Last Name": None,
            "Last Occupant": airtable_record["fields"]["Preferred Name"],
            "netid": None,
            "Preferred Name": app.next_vacancy,
            "Search Status": "Recently Vacated",
            "Start Date": None,
            "University ID": None,
            "University Phone": None
        }
        app.table.update(airtable_record['id'], data)
        print(f'Created {data["Preferred Name"]} (was {airtable_record["Preferred Name"]})')

    @property
    def next_vacancy(self):
        if not self._next_vacancy_number:
            formula = "REGEX_MATCH({Preferred Name}, '^__VACANCY')"
            records = self.table.all(formula=formula, sort=["Preferred Name"])
            last = sub(r"[^\d]", "", records[-1]["fields"]["Preferred Name"])
            self._next_vacancy_number = int(last)+1
        else:
            self._next_vacancy_number+=1
        return f'__VACANCY_{str(self._next_vacancy_number).zfill(3)}__'

    def _get_record_from_report_by_emplid(self, emplid):
        for row in self._src_data:
            if row['Emplid'] == emplid:
                return row

    def _all_emplids_from_airtable(self):
        ids = self.table.all(fields=('University ID'))
        return [i['fields']['University ID'] for i in ids if i['fields'].get('University ID')]

    def _all_emplids_from_report(self):
        return [row['Emplid'] for row in self._src_data]

    def _netid_from_ldap(self, employee_id):
        return self._ldap.query(employee_id, 'universityid')['uid']

    def _add_new_record(self, csv_row):
        csv_row = SrcRow(csv_row)
        airtable_record = self.get_airtable_record_by_emplid(csv_row.emplid)
        if airtable_record:
            name = airtable_record['Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            data = App._map_csv_row_to_airtable_fields(csv_row)
            self.table.create(data)
            print(f'Added {csv_row.emplid} ({csv_row["Name"]})')

    @staticmethod
    def _load_private(pth='./private.json'):
        with open(pth, 'r') as f:
            return load(f)

    @staticmethod
    def _load_src_data(src_data_path):
        with open(src_data_path, 'r', encoding='utf-16') as f: # Note encoding
            return list(DictReader(f, delimiter='\t'))

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
    def _map_csv_row_to_airtable_fields(csv_row, scrape_photo=False, update=False):
        'update=True will exclude University ID and Preferred Name'
        # TODO: What would a better report have?
        # * Long Title
        # * netid
        # Funding source
        try:
            data = {}
            if not update:
                data['University ID'] = csv_row.emplid
            data['Division'] = csv_row['Department Name']
            data['Admin. Group'] = csv_row.admin_group
            data['Search Status'] = 'Hired'
            phone = csv_row.phone
            if phone:
                data['University Phone'] = phone
            data['End Date'] = csv_row.term_end
            data['Term/Perm/CA Track'] = csv_row.term_perm
            data['Title'] = csv_row['Position - Job Title']
            data['Email'] = csv_row['E-Mail']
            if not update:
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

    report = './Alpha Roster.csv'
    # TODO: make Report an object with many Source Rows
    # TODO: make Airtable an object
    app = App(report)
    # app.check_all_eplids_from_report_in_airtable() # prints warnings
    # app.check_all_eplids_from_airtable_in_report() # prints warnings
    app.employee_to_vacancy('940007715')
    # TODO: Check position numbers?
    # app.sync_airtable_with_report()
    # app.update_supervisor_hierarchy()

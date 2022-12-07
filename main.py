from bs4 import BeautifulSoup
from json import load
from requests import get
from staff_management.ldap import LDAP
from staff_management.staff_airtable import StaffAirtable
from staff_management.staff_report import StaffReport
from sys import stderr
from sys import stdout
from time import sleep

THROTTLE_INTERVAL = 0.2

class App():
    def __init__(self, src_data_path):
        conf = App._load_private()
        self._airtable = StaffAirtable(conf["API_KEY"], conf["BASE_ID"], conf["MAIN_TABLE_ID"], conf["DEPARTED_TABLE_ID"])
        self._staff_report = StaffReport(src_data_path)
        self._ldap = LDAP(conf["LDAP_HOST"], conf["LDAP_OC"])
        
    def sync_airtable_with_report(self, scrape_photo=False):
        for r in self._staff_report.rows:
            airtable_record = self._airtable.get_record_by_emplid(r.emplid)
            log = False
            if not airtable_record:
                # If there's a vacancy w/ this position number, use that vacancy
                position_no = r.position_number 
                if position_no:
                    log = True
                    airtable_record = self._airtable.get_record_by_position_no(position_no)
            if airtable_record:
                data = self._map_report_row_to_airtable_fields(r, scrape_photo=scrape_photo)
                self._airtable.update_record(airtable_record['id'], data, log=log)
            else:
                data = self._map_report_row_to_airtable_fields(r, scrape_photo=True)
                self._airtable.add_new_record(data)
                sleep(THROTTLE_INTERVAL)

    def update_supervisor_hierarchy(self):
        self._airtable.update_supervisor_hierarchy(self._staff_report, THROTTLE_INTERVAL)

    def employee_to_vacancy(self, emplid):
        return self._airtable.employee_to_vacancy(emplid)

    def check_all_emplids_from_report_in_airtable(self):
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._staff_report.all_emplids
        missing_from_airtable = [i for i in report_emplids if i not in airtable_emplids]
        for emplid in missing_from_airtable:
            name = self._staff_report.get_record_by_emplid(emplid)["Name"]
            print(f'Employee {emplid} ({name}) is missing from Airtable; #sync_airtable_with_report() will add them.')
        
    def check_all_emplids_from_airtable_in_report(self):
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._staff_report.all_emplids
        missing_from_report = [i for i in airtable_emplids if i not in report_emplids]
        for emplid in missing_from_report:
            name = self._airtable.get_record_by_emplid(emplid)['fields'].get('Preferred Name')
            if name != "Anne Jarvis":
                print(f'Employee {emplid} ({name}) is missing from CSV Report; #employee_to_vacancy(emplid) will remove them.')

    def check_all_position_numbers_from_report_in_airtable(self):
        airtable_pns = self._airtable.all_position_numbers
        report_pns = self._staff_report.all_position_numbers
        missing_from_airtable = [pn for pn in report_pns if pn not in airtable_pns]
        for pn in missing_from_airtable:
            name = self._staff_report.get_record_by_position_no(pn)["Name"]
            print(f'Position Number {pn} ({name}) is missing from Airtable.')

    def check_all_position_numbers_from_airtable_in_report(self):
        airtable_pns = self._airtable.all_position_numbers
        report_pns = self._staff_report.all_position_numbers
        missing_from_report = [pn for pn in airtable_pns if pn not in report_pns]
        for pn in missing_from_report:
            name = self._airtable.get_record_by_position_no(pn)['fields'].get('Preferred Name')
            if not name.startswith('__VACANCY'):
                print(f'Position Number {pn} ({name}) is missing from CSV Report.')

    def _map_report_row_to_airtable_fields(self, report_row, scrape_photo=False):
        # TODO: What would a better report have?
        # * Better Title
        # * netid
        # * Funding source
        try:
            data = {}
            data['University ID'] = report_row.emplid
            data['Division'] = report_row['Department Name']
            data['Admin. Group'] = report_row.admin_group
            data['Search Status'] = 'Hired'
            data['University Phone'] = report_row.phone
            data['End Date'] = report_row.term_end
            data['Term/Perm/CA Track'] = report_row.term_perm
            data['Title'] = report_row['Position - Job Title']
            data['Email'] = report_row['E-Mail']
            data['Last Name'] = report_row.last_name
            data['First Name'] = report_row.first_name
            data['Time'] = report_row.time
            data['Start Date'] = report_row.start_date
            data['Grade'] = report_row.grade
            data['Sal. Plan'] = report_row['Sal Plan']
            data['Position Number'] = report_row.position_number
            data['Address'] = report_row.address
            netid = self._ldap.netid(report_row.emplid)
            data['netid'] = netid
            data['Preferred Name'] = report_row.preferred_name
            if scrape_photo:
                thumbnail = App._get_thumbnail_url(netid)
                if thumbnail:
                    data['Headshot'] = [ {'url': thumbnail} ]
                else:
                    data['Headshot'] = [ {'url': StaffAirtable.NO_PHOTO_IMAGE} ]
            return data
        except Exception as e:
            print(f'Error with emplid {report_row.emplid}', file=stderr)
            raise e

    def run_checks(self):
        #TODO: this could prompt to add/remove people as it goes...
        self.check_all_emplids_from_report_in_airtable() # prints warnings
        self.check_all_emplids_from_airtable_in_report() # prints warnings
        self.check_all_position_numbers_from_report_in_airtable() # prints warnings
        self.check_all_position_numbers_from_airtable_in_report() # prints warnings

    @staticmethod
    def _load_private(pth='./private.json'):
        with open(pth, 'r') as f:
            return load(f)

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


def print_json(json_payload, f=stdout):
    # For debugging
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

if __name__ == '__main__':
    report = './Alpha Roster.csv'
    app = App(report)

    # app.run_checks()
    # app.employee_to_vacancy('940003890') # updates and prints warnings
       
    # TODO: check all position numbers are unique in airtable
    # TODO: Log adds and updates.

    # app.sync_airtable_with_report(scrape_photo=False) # updates
    app.update_supervisor_hierarchy() # updates and prints warnings

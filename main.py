from csv import DictReader
from json import load
from staff_management.earnings_detail_report import EarningsDetailReport
from staff_management.staff_airtable import StaffAirtable
from staff_management.staff_report import StaffReport
from sys import stderr
from sys import stdout
from time import sleep

THROTTLE_INTERVAL = 0.2

class App():
    def __init__(self, src_data_path):
        conf = App._load_private()
        self._airtable = StaffAirtable(conf["PAT"], conf["BASE_ID"], conf["ALL_STAFF_TABLE_ID"], conf['REMOVAL_TABLE_ID'])
        self._staff_report = StaffReport(src_data_path)

    @property
    def all_vacancies(self):
        return self._airtable.all_vacancies
        
    def sync_airtable_with_report(self):
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
                data = self._map_report_row_to_airtable_fields(r)
                if airtable_record['fields']['pul:Preferred Name'].startswith('__VACANCY'):
                    data = self._map_report_row_to_airtable_fields(r)
                # TODO: check that position number has not changed here. If it has, log to convert the person to a vacancy first, and exit.
                if r.position_number != airtable_record['fields']['Position Number']:
                    emplid = r.emplid
                    preferred_name = airtable_record['fields']['pul:Preferred Name']
                    message = f'''Position Number for {preferred_name} (emplid {emplid}) has changed.
Consider converting the employee in their current position to a vacancy first with
app.employee_to_vacancy(\'{emplid}\')'''
                    exit(message)
                self._airtable.update_record(airtable_record['id'], data, log=log)
            else: # this is a NEW record
                if r.position_number == '[N/A - DoF]':
                    message = f'''{r.preferred_name} is a new DoF Employee. Change this vacancy manually before proceeding'''
                    exit(message)
                data = self._map_report_row_to_airtable_fields(r)
                self._airtable.add_new_record(data)
                sleep(THROTTLE_INTERVAL)

    def update_supervisor_info(self):
        # 1: Clear all
        # 2. Update supervisor hierarchy (uses CSV report)
        # 3. Update pula managers (uses Airtable)
        # 4. Update DoF managers (uses Airtable)
        self._airtable.clear_supervisor_statuses()
        self._airtable.update_supervisor_hierarchy(self._staff_report, THROTTLE_INTERVAL)
        self._airtable.update_pula_supervisor_statuses()
        self._airtable.update_dof_librarian_supervisor_statuses()

    def employee_to_vacancy(self, emplid):
        return self._airtable.employee_to_vacancy(emplid)

    def check_all_emplids_from_report_in_airtable(self):
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._staff_report.all_emplids
        missing_from_airtable = [i for i in report_emplids if i not in airtable_emplids]
        for emplid in missing_from_airtable:
            report_record = self._staff_report.get_record_by_emplid(emplid)
            name = report_record["Name"]
            if report_record.position_number == "[N/A - DoF]":
                print(f'Employee {emplid} ({name}) is a new DoF Employee; the vacancy will need to be updated manually.', file=stderr)
                exit(1)
            print(f'Employee {emplid} ({name}) is missing from Airtable; #sync_airtable_with_report() will add them.')
        
    def check_all_emplids_from_airtable_in_report(self):
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._staff_report.all_emplids
        missing_from_report = [i for i in airtable_emplids if i not in report_emplids]
        for emplid in missing_from_report:
            name = self._airtable.get_record_by_emplid(emplid)['fields'].get('pul:Preferred Name')
            if name != "Anne Jarvis":
                print(f'Employee {emplid} ({name}) is missing from CSV Report; app.employee_to_vacancy(\'{emplid}\') will remove them.')

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
            at_record = self._airtable.get_record_by_position_no(pn)
            name = at_record['fields'].get('pul:Preferred Name')
            emplid = at_record['fields'].get('University ID')
            is_vacancy = name.startswith('__VACANCY')
            is_anne = pn == '00003305'
            if not is_vacancy and not is_anne:
                print(f'Position Number {pn} ({name}) is missing from CSV Report; app.employee_to_vacancy(\'{emplid}\') will remove them.')

    def _map_report_row_to_airtable_fields(self, report_row):
        try:
            data = {}
            data['University ID'] = report_row.emplid
            data['Division'] = report_row.division
            data['Admin. Group'] = report_row.admin_group
            data['pul:Search Status'] = 'Hired'
            data['University Phone'] = report_row.phone
            data['End Date'] = report_row.term_end
            data['Term/Perm/CA Track'] = report_row.term_perm
            data['Title'] = report_row.title
            data['pul:Preferred Name'] = report_row.preferred_name
            data['Email'] = report_row.email
            data['Last Name'] = report_row.last_name
            data['First Name'] = report_row.first_name
            data['Time'] = report_row.time
            data['Start Date'] = report_row.start_date
            data['Rehire Date'] = report_row.rehire_date
            data['Grade'] = report_row.grade
            data['Sal. Plan'] = report_row.get('Sal Plan')
            data['Position Number'] = report_row.position_number
            data['Address'] = report_row.address
            netid = report_row['Net ID']
            data['netid'] = netid
            data['PS Department Name'] = report_row.ps_department_name
            data['PS Department Code'] = report_row.ps_department_code

        except Exception as e:
            print(f'Error with emplid {report_row.emplid}', file=stderr)
            raise e
        
        return data

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

def print_json(json_payload, f=stdout):
    # For debugging
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

if __name__ == '__main__':
    # This is the Library Alpha Roster report from the Information Warehouse.
    app = App('./Alpha Roster.csv')
    # app.run_checks()
    # app.employee_to_vacancy('940007217')
    # app.sync_airtable_with_report() # updates
    app.update_supervisor_info() # takes a long time
    
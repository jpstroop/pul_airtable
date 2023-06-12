from copy import deepcopy
from pyairtable import Table
from re import sub
from sys import stderr
from sys import stdout
from time import sleep

class StaffAirtable():
    
    VACANT_IMAGE = 'https://github.com/jpstroop/pul_airtable/blob/main/vacant.png'
    NO_PHOTO_IMAGE = 'https://github.com/jpstroop/pul_airtable/blob/main/no_photo.png'

    def __init__(self, personal_access_token, base_id, all_staff_table_id):
        self._main_table = Table(personal_access_token, base_id, all_staff_table_id)
        self._next_vacancy_number = None

    @property
    def next_vacancy(self):
        if not self._next_vacancy_number:
            formula = "REGEX_MATCH({pul:Preferred Name}, '^__VACANCY')"
            records = self._main_table.all(formula=formula, sort=["pul:Preferred Name"])
            last = sub(r"[^\d]", "", records[-1]["fields"]["pul:Preferred Name"])
            self._next_vacancy_number = int(last)+1
        else:
            self._next_vacancy_number+=1
        return f'__VACANCY_{str(self._next_vacancy_number).zfill(3)}__'

    @property
    def all_emplids(self):
        ids = self._main_table.all(fields=('University ID'))
        return [i['fields']['University ID'] for i in ids if i['fields'].get('University ID')]

    @property
    def all_position_numbers(self):
        nos = self._main_table.all(fields=('Position Number'))
        filt = lambda pn: not pn.startswith('[') and pn != ""
        return list(filter(filt, [n['fields'].get('Position Number', "") for n in nos]))

    @property
    def all_vacancies(self):
        formula = "REGEX_MATCH({pul:Preferred Name}, '^__VACANCY')"
        return self._main_table.all(formula=formula, sort=["pul:Preferred Name"])

    @property
    def all_vacancy_position_ids(self):
        '''This is the position number for HR jobs, and the name of the last 
        occupant for DoF jobs.
        '''
        pass

    def get_record_by_emplid(self, emplid):
        return self._main_table.first(formula=f'{{University ID}} = "{emplid}"')

    def get_record_by_position_no(self, pn):
        return self._main_table.first(formula=f'{{Position Number}} = "{pn}"')

    def add_new_record(self, data, by_pn=False):
        emplid = data['University ID']
        if self.get_record_by_emplid(emplid):
            name = airtable_record['pul:Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            self._main_table.create(data)
            print(f'Added {emplid} ({data["pul:Preferred Name"]})')

    def update_record(self, record_id, data, log=False):
        if log:
            position_no = data.get('Position Number')
            emplid = data['University ID']
            print(f'Updated position {position_no} with {emplid} ({data["pul:Preferred Name"]})')
        self._main_table.update(record_id, data)

    def employee_to_vacancy(self, emplid):
        airtable_record = self.get_record_by_emplid(emplid)
        record_copy = deepcopy(airtable_record['fields'])
        record_copy.pop('Manager/Supervisor', None)
        record_copy.pop('Headshot', None)
        record_copy.pop('Anniversary?', None)
        # self._departed_table.create(record_copy, typecast=True) # might need a check if exists, but let's try w/o
        data =  {
            "Email": None,
            "First Name": None,
            "Headshot": [ {'url': StaffAirtable.VACANT_IMAGE} ],
            "Last Name": None,
            "Last Occupant": airtable_record["fields"]["pul:Preferred Name"],
            "netid": None,
            "pul:Preferred Name": self.next_vacancy,
            "pul:Search Status": "Recently Vacated",
            "Start Date": None,
            "University ID": None,
            "University Phone": None,
            "FWA/Hours": None
        }
        self._main_table.update(airtable_record['id'], data)
        print(f'Created {data["pul:Preferred Name"]} (was {airtable_record["fields"]["pul:Preferred Name"]})')

    def update_supervisor_hierarchy(self, staff_report, throttle_interval):
        for empl, supr in staff_report.supervisor_hierarchy:
            try:
                employee_record = self.get_record_by_emplid(empl) # TODO: Will error if not found
                supervisor_record = self.get_record_by_emplid(supr)
                updates = [{
                    "id" : supervisor_record['id'],
                    "fields" : { "Is Supervisor?" : True }
                },{
                    "id" : employee_record['id'],
                    "fields" : {
                        "Manager/Supervisor" : [ supervisor_record['id'] ]
                    }
                }]
                self._main_table.batch_update(updates)
            except Exception as e:
                empl_name = employee_record['fields']['pul:Preferred Name']
                if supervisor_record is None:
                    print(f"{empl_name} lacks a supervisor", file=stderr)
                else:
                    print(f"Error with {empl_name}", file=stderr)
                    print(f"Original Error: {str(e)}", file=stderr)
            sleep(throttle_interval)

# For debugging
def print_json(json_payload, f=stdout):
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

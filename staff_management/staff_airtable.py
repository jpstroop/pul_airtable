from pyairtable import Table
from re import sub
from sys import stderr
from sys import stdout
from time import sleep

class StaffAirtable():
    
    VACANT_IMAGE = 'https://dl.airtable.com/.attachments/d5340fc21c451f1733d6ebfff1c79d70/897912fb/Vacant.png'
    NO_PHOTO_IMAGE = 'https://dl.airtable.com/.attachmentThumbnails/6285b261926b8d097fe02a5639817553/e08f234a.png'

    def __init__(self, api_key, base_id, table_id):
        self._table = Table(api_key, base_id, table_id)
        self._next_vacancy_number = None

    @property
    def next_vacancy(self):
        if not self._next_vacancy_number:
            formula = "REGEX_MATCH({Preferred Name}, '^__VACANCY')"
            records = self._table.all(formula=formula, sort=["Preferred Name"])
            last = sub(r"[^\d]", "", records[-1]["fields"]["Preferred Name"])
            self._next_vacancy_number = int(last)+1
        else:
            self._next_vacancy_number+=1
        return f'__VACANCY_{str(self._next_vacancy_number).zfill(3)}__'

    @property
    def all_emplids(self):
        ids = self._table.all(fields=('University ID'))
        return [i['fields']['University ID'] for i in ids if i['fields'].get('University ID')]

    @property
    def all_position_numbers(self):
        nos = self._table.all(fields=('Position Number'))
        filt = lambda pn: not pn.startswith('[') and pn != ""
        return list(filter(filt, [n['fields'].get('Position Number', "") for n in nos]))

    @property
    def all_vacancy_position_numbers(self):
        pass

    def get_record_by_emplid(self, emplid):
        return self._table.first(formula=f'{{University ID}} = "{emplid}"')

    def get_record_by_position_no(self, pn):
        return self._table.first(formula=f'{{Position Number}} = "{pn}"')

    def add_new_record(self, data, by_pn=False):
        emplid = data['University ID']
        if self.get_record_by_emplid(emplid):
            name = airtable_record['Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            self._table.create(data)
            print(f'Added {emplid} ({data["Preferred Name"]})')

    def update_record(self, record_id, data, log=False):
        if log:
            position_no = data.get('Position Number')
            emplid = data['University ID']
            print(f'Updated position {position_no} with {emplid} ({data["Preferred Name"]})')
        self._table.update(record_id, data)

    def employee_to_vacancy(self, emplid):
        airtable_record = self.get_record_by_emplid(emplid)
        data =  {
            "Address": None,
            "Email": None,
            "First Name": None,
            "Headshot": [ {'url': StaffAirtable.VACANT_IMAGE} ],
            "Last Name": None,
            "Last Occupant": airtable_record["fields"]["Preferred Name"],
            "netid": None,
            "Preferred Name": self.next_vacancy,
            "Search Status": "Recently Vacated",
            "Start Date": None,
            "University ID": None,
            "University Phone": None,
            "FWA/Hours": None
        }
        self._table.update(airtable_record['id'], data)
        print(f'Created {data["Preferred Name"]} (was {airtable_record["fields"]["Preferred Name"]})')

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
                self._table.batch_update(updates)
                # TODO: could build a big struct at once if we wanted (above), rather than row by row
            except Exception as e:

                print("****Error****", file=stderr)
                print('Employee record:', file=stderr)
                print_json(employee_record, f=stderr)
                print('Supervisor record:', file=stderr)
                print_json(supervisor_record, f=stderr)
                print(f"Original Error: {str(e)}", file=stderr)
                #TODO likely a missing supervisor. Print name from CSV?
            sleep(throttle_interval)

def print_json(json_payload, f=stdout):
    # For debugging
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

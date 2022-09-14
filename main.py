from csv import DictReader
from datetime import date
from json import load
from ldap import LDAP_API
from pyairtable import Table
from sys import stderr
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
        airtable_record = app.get_by_emplid(row.emplid)
        if airtable_record:
            name = airtable_record['Preferred Name']
            raise Exception(f'A record already exists for {emplid} ({name})')
        else:
            data = App._map_csv_row_to_airtable_fields(row)
            # table.create(data)

    @staticmethod
    def _map_csv_row_to_airtable_fields(csv_row):
        try:
            data = {}
            data['University ID'] = csv_row.emplid
            data['Division Code'] = csv_row['Dept']
            data['Division Name'] = csv_row['Department Name']
            data['Admin. Unit'] = csv_row.admin_unit
            data['Search Status'] = 'Hired'
            data['University Phone'] = csv_row.phone
            # data['Reporting to'] = [] # TODO, come back and query by emplid
            data['Term'] = csv_row.term_end
            data['Title'] = csv_row['Position - Job Title']
            data['Email'] = csv_row['E-Mail']
            data['Preferred Name'] = csv_row.preferred_name
            data['Last Name'] = csv_row.last_name
            data['First Name'] = csv_row.first_name
            data['Time'] = csv_row.time
            data['Start Date'] = csv_row.start_date
            data['Grade'] = csv_row['Grade'] # TODO: leading 0 on ADM, AIT, BLB
            data['Sal. Plan'] = csv_row['Sal Plan']
            data['Postion Number'] = csv_row.position_number
            data['Address'] = csv_row['Telephone DB Office Location']
            data['netid'] = app.netid_from_ldap(csv_row.emplid)
            return data
        except Exception as e:
            print('*'*80)
            print(f'Error with emplid {csv_row.emplid}')
            print('*'*80)
            raise e


    # TODO: be able to hand this a report and have it decide what fields to
    # update, records to add, and report when an employee is no longer on in the
    # report but still in airtable. Should also be able to validate the report
    # in case the fields have changed

class SrcRow():
    '''A row from the Alpha Roster - Job and Personal Data - Point in Time Report
    '''
    def __init__(self, row):
        self._row = row

    def __getitem__(self, key):
        return self._row[key]

    @staticmethod
    def parse_date(s):
        # handles "MM/DD/YY (0:00)"
        # m, d, y = map(int, s.split(" ")[0].split("/"))
        # y = y+2000 if y <= 22 else y+1900
        # return date(y, m, d)
        return date.fromisoformat(s.split(" ")[0])

    @property
    def emplid(self):
        return self._row['Emplid'].zfill(9)

    @property
    def admin_unit(self):
        sal_pln = self._row['Sal Plan Descr']
        if sal_pln.startswith('Library Support'):
            return 'HR: PULA'
        elif sal_pln.startswith('Reg Prof Specialist'):
            return 'DoF: Professional Specialist'
        elif sal_pln.startswith('Regular Professional Library'):
            return 'DoF: Librarian'
        else:
            return 'HR: Non-Bargaining'

    @property
    def phone(self):
        if self._row['OL1 Phone - Phone Number']:
            local = self._row['OL1 Phone - Phone Number'].split('/')[1]
            return f"(609) {local}"
        else:
            return None

    @property
    def term_end(self):
        field_data = self._row["Estimated Appt End Date"]
        if not field_data:
            return "[N/A - Permanent]"
        else:
            return SrcRow.parse_date(field_data)

    @property
    def preferred_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def first_name(self):
        field_data = self._row['Name']
        return field_data.split(',')[1].split(' ')[0] # drops initial

    @property
    def last_name(self):
        field_data = self._row['Name']
        return field_data.split(',')[0].split(' ')[0] # drops Jr, III, etc,

    @property
    def time(self):
        return float(self._row['FTE'])

    @property
    def start_date(self):
        return SrcRow.parse_date(self._row['Hire Date'])

    @property
    def position_number(self):
        if self._row['Position Number']:
            return self._row['Position Number']
        else:
            return '[N/A - DoF]'


def print_json(json_payload):
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2, default=str))

# TODO: a second pass, linking supervisors via emplid, and marking "is supervisor"

if __name__ == '__main__':

    app = App()
    # Load CSV.
    with open('./Alpha Roster - Job and Personal Data - Point in Time af16125ca.csv', 'r') as f:
        src_data = list(DictReader(f))
    # For each row:
    for r in src_data:
        csv_row = SrcRow(r)
        print_json(App._map_csv_row_to_airtable_fields(csv_row))

        # # If a record already exists
        # airtable_record = app.get_by_emplid(csv_row.emplid)
        # if airtable_record:
        #     # update the Department:
        #     data = {
        #         'Division Code' : csv_row['Dept'],
        #         'Division Name' : csv_row['Department Name']
        #     }
        #     table.update(airtable_record['id'], data)
        # #  If it does not:
        # else:
        #     app.add_new_record(csv_row)
        #     sleep(THROTTLE_INTERVAL)

# Sample record:
# {
#     "id": "recyud4oppeMNKqUO",
#     "createdTime": "2021-12-03T17:31:10.000Z",
#     "fields": {
# x       "Grade": "030",
# n/a      "FWA/Hours": "FT Remote; 7:30am-3:30pm",
# x      "University ID": "940004568",
# x      "Admin. Unit": "HR: Non-Bargaining",
# x      "Search Status": "Hired",
# x      "University Phone": "(609) 258-1378",
# x      "Reporting to": [
#         "recxNFKOveTGZu4sZ"
#       ],
# x     "Term": "[N/A - Permanent]",
# x      "Last Occupant": "[new from Provost]",
# x      "Title": "Research Data Infrastructure Developer",
# x      "Email": "carolyn.cole@princeton.edu",
# x      "Preferred Name": "Carolyn A. Cole",
# x      "Last Name": "Cole",
# x      "First Name": "Carolyn",
# x      "Time": 1,
# x      "Start Date": "2019-04-15",
# x      "Note/Status": "  #2022-14008      3/18/2022 Carolyn Cole accepted the offer. Cole will transfer on 4/18/2022\n\n",
# x      "Sal. Plan": "AIT",
# x      "Unit": "Research Data and Scholarship Services",
# x      "Position Number": "9484  (old 4887)",
# x      "netid": "cac9",
#       "Headshot": [
#         {
#           "id": "attjZNhL2qwGngOyV",
#           "width": 150,
#           "height": 200,
#           "url": "https://dl.airtable.com/.attachments/37c3e3d55609bb2d96e8a5d622f985d6/43feb183/CarolynCole.jfif",
#           "filename": "Carolyn Cole.jfif",
#           "size": 10614,
#           "type": "image/jpeg",
#           "thumbnails": {
#             "small": {
#               "url": "https://dl.airtable.com/.attachmentThumbnails/de04e14abcbfa45553441b393f8a2de2/65a707e7",
#               "width": 27,
#               "height": 36
#             },
#             "large": {
#               "url": "https://dl.airtable.com/.attachmentThumbnails/0756bf2dc03661b9b85e35fd32f6fb18/c127a86c",
#               "width": 150,
#               "height": 200
#             },
#             "full": {
#               "url": "https://dl.airtable.com/.attachmentThumbnails/f5864fe26f6ff5532ea747a18eb6f29f/38bb30e9",
#               "width": 3000,
#               "height": 3000
#             }
#           }
#         }
#       ]
#       "Anniversary?": "No",
#     }

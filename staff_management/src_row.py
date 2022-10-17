from datetime import date

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
        return str(date.fromisoformat(s.split(" ")[0]))

    @property
    def emplid(self):
        return self._row['Emplid'].zfill(9)

    @property
    def super_emplid(self):
        return self._row['Manager/Supervisor Emplid'].zfill(9)

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
    def term_perm(self):
        end = self._row["Estimated Appt End Date"]
        sal_plan = self._row["Sal Plan"]
        if end and sal_plan == "LR":
            return "CA Track"
        elif not end:
            return "Permanent"
        else:
            return "Term"
    

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
        last = field_data.split(',')[0]
        if not last.startswith("Al "): # keep, e.g., "Al Amin"
            last = last.split(' ')[0] # drops Jr, III, etc,
        return last

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

    @property
    def grade(self):
        grade = self._row['Grade']
        if self._row['Sal Plan'] in ('ADM', 'AIT', 'BLB'):
            grade = f'0{grade}'
        return grade

from datetime import date
from sys import stderr

DIVISION_LOOKUP = {
    "Center for Digital Humanities":"Center for Digital Humanities",
    "Lib-Collections & Access Svcs":"Collections and Access Services",
    "Lib-Data, Rsrch&Teaching Svcs":"Data, Research, and Teaching Services",
    "Lib-Research Coll & Presr Cons":"ReCAP",
    "Lib-Rsrch,Data &Open Schlrshp":"Research, Data, and Open Scholarship",
    "Library - Main":"Office of the University Librarian",
    "Library-Deputy Univ Librarian":"Office of the Deputy Dean of Libraries",
    "Library-Finance&Acquistns Svcs":"Finance and Acquisitions Services",
    "Library-Special Collections":"Special and Distinctive Collections",
    # "Library-Research & Instr Svcs":"Library Research and Instruction Services",
}
    

class ReportRow():
    '''A row from the Alpha Roster - Job and Personal Data - Point in Time Report
    '''
    def __init__(self, row):
        self._row = {}
        for k,v in row.items():
            # We do this so that empty fields raise KeyError or can use get()
            # properly. The TSV parser leaves whitespace in otherwise empty
            # fields
            v = v.strip()
            if v != "":
                self._row[k] = v

    def __getitem__(self, key):
        return self._row[key]


    def get(self, key, default=None):
        return self._row.get(key, default)

    @staticmethod
    def parse_date(s):
        if "/" in s:
            m, d, y = map(int, s.split(" ")[0].split("/"))
            # y = y+2000 if y <= 22 else y+1900 - it seems we can assume we'll get a 4 digit year
            return str(date(y, m, d))
        # return date(y, m, d)
        return str(date.fromisoformat(s.split(" ")[0]))

    @property
    def emplid(self):
        return self._row['Emplid'].zfill(9)

    @property
    def super_emplid(self):
        emplid = self._row.get('Manager/Supervisor Emplid')
        if emplid:
            return emplid.zfill(9)
        else:
            return None

    @property
    def admin_group(self):
        sal_pln = self._row.get('Sal Plan Descr')
        if sal_pln is None:
            print(f"{self.emplid} lacks a Sal Plan Descr in the staff report")
            return None
        elif sal_pln.startswith('Library Support'):
            return 'HR: PULA'
        elif sal_pln.startswith('Reg Prof Specialist'):
            return 'DoF: Professional Specialist'
        elif sal_pln.startswith('Regular Professional Library'):
            return 'DoF: Librarian'
        else:
            return 'HR: Non-Bargaining'

    @property
    def phone(self):
        data = self._row.get('OL1 Phone - Phone Number')
        if data:
            local = data.split('/')[1]
            return f"(609) {local}"
        else:
            return None

    @property
    def term_end(self):
        return self._row.get("Estimated Appt End Date")

    @property
    def term_perm(self):
        end = self._row.get("Estimated Appt End Date")
        sal_plan = self._row.get("Sal Plan")
        if sal_plan is None:
            print(f"{self.emplid} lacks a Sal Plan in the staff report")
            return None
        if end and sal_plan == "LR":
            return "CA Track"
        elif self._row["Staff"] == "Casual Hourly":
            return "Casual Hourly"
        elif not end:
            return "Permanent"
        else:
            return "Term"

    @property
    def title(self):
        pref_title = self._row.get('Admin Post Title')
        if pref_title:
            return pref_title
        else:
            return self._row.get('Position - Job Title')

    @property
    def preferred_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def first_name(self):
        return self._row['Preferred Else Primary First Name']

    @property
    def last_name(self):
        return self._row['Preferred Else Primary Last Name']
    
    @property
    def email(self):
        return self._row['E-Mail Address - Campus']

    @property
    def time(self):
        return float(self._row['FTE'])

    @property
    def start_date(self):
        return ReportRow.parse_date(self._row['Hire Date'])

    @property
    def rehire_date(self):
        return ReportRow.parse_date(self._row['Rehire Date'])

    @property
    def address(self):
        return self.get('Telephone DB Office Location')

    @property
    def position_number(self):
        if self._row.get('Position Number'):
            return self._row['Position Number']
        elif self.term_perm == "Casual Hourly":
            return "[N/A - Casual]"
        else:
            return '[N/A - DoF]'

    @property
    def grade(self):
        grade = self._row.get('Grade')
        if grade:
            grade = int(grade)
        return grade

    @property
    def division(self):
        return DIVISION_LOOKUP[self._row['Department Name']]
    
    @property
    def ps_department_name(self):
        return self._row['Department Name']
        
    @property
    def ps_department_code(self):
        return self._row['Dept']
from csv import DictReader
from staff_management.report_row import ReportRow

class StaffReport():
    def __init__(self, file_path):
        with open(file_path, 'r', encoding='utf-16') as f: # Note encoding
            self.rows = [ReportRow(r) for r in DictReader(f, delimiter='\t')]

    def get_record_by_emplid(self, emplid):
        for row in self.rows:
            if row['Emplid'] == emplid:
                return row
        return None

    def get_record_by_position_no(self, pn):
        for row in self.rows:
            if row.get('Position Number') == pn:
                return row
        return None

    @property
    def supervisor_hierarchy(self):
        return [(r.emplid, r.super_emplid) for r in self.rows]

    @property
    def all_emplids(self):
        return [row['Emplid'] for row in self.rows]

    @property
    def all_position_numbers(self):
        return [r['Position Number'] for r in self.rows if r.get('Position Number')]


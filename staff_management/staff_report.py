# Standard library imports
from csv import DictReader
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

# Local imports
from staff_management.report_row import ReportRow


class StaffReport:
    rows: List[ReportRow]

    def __init__(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-16") as f:  # Note encoding
            self.rows = [ReportRow(r) for r in DictReader(f, delimiter="\t")]

    def get_record_by_emplid(self, emplid: str) -> Optional[ReportRow]:
        for row in self.rows:
            if row["Emplid"] == emplid:
                return row
        return None

    def get_record_by_position_no(self, pn: str) -> Optional[ReportRow]:
        for row in self.rows:
            if row.get("Position Number") == pn:
                return row
        return None

    @property
    def supervisor_hierarchy(self) -> List[Tuple[str, Optional[str]]]:
        return [(r.emplid, r.super_emplid) for r in self.rows]

    @property
    def grouped_supervisor_hierarchy(self) -> Dict[Optional[str], List[str]]:
        d: Dict[Optional[str], List[str]] = {}
        for employee, supervisor in self.supervisor_hierarchy:
            d.setdefault(supervisor, []).append(employee)
        return d

    @property
    def all_emplids(self) -> List[str]:
        return [row["Emplid"].zfill(9) for row in self.rows]

    @property
    def all_position_numbers(self) -> List[str]:
        return [r["Position Number"] for r in self.rows if r.get("Position Number")]

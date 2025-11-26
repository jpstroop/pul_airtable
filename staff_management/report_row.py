# Standard library imports
from datetime import date
from sys import stderr
from typing import Dict
from typing import Optional

DIVISION_LOOKUP: Dict[str, str] = {
    "Center for Digital Humanities": "Center for Digital Humanities",
    "Lib-Collections & Access Svcs": "Collections and Access Services",
    "Lib-Data, Rsrch&Teaching Svcs": "Data, Research, and Teaching Services",
    "Lib-Research Coll & Presr Cons": "ReCAP",
    "Lib-Rsrch,Data &Open Schlrshp": "Research, Data, and Open Scholarship",
    "Library - Main": "Office of the University Librarian",
    "Library-Deputy Univ Librarian": "Office of the Deputy Dean of Libraries",
    "Library-Finance&Acquistns Svcs": "Finance and Acquisitions Services",
    "Library-Special Collections": "Special and Distinctive Collections",
}


class ReportRow:
    """A row from the Alpha Roster - Job and Personal Data - Point in Time Report"""

    _row: Dict[str, str]

    def __init__(self, row: Dict[str, str]) -> None:
        self._row = {}
        for k, v in row.items():
            # We do this so that empty fields raise KeyError or can use get()
            # properly. The TSV parser leaves whitespace in otherwise empty
            # fields
            v = v.strip()
            if v != "":
                self._row[k] = v

    def __getitem__(self, key: str) -> str:
        return self._row[key]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._row.get(key, default)

    @staticmethod
    def parse_date(s: str) -> str:
        if "/" in s:
            m, d, y = map(int, s.split(" ")[0].split("/"))
            # y = y+2000 if y <= 22 else y+1900 - it seems we can assume we'll get a 4 digit year
            return str(date(y, m, d))
        # return date(y, m, d)
        return str(date.fromisoformat(s.split(" ")[0]))

    @property
    def emplid(self) -> str:
        return self._row["Emplid"].zfill(9)

    @property
    def super_emplid(self) -> Optional[str]:
        emplid = self._row.get("Manager/Supervisor Emplid")
        if emplid:
            return emplid.zfill(9)
        else:
            return None

    @property
    def admin_group(self) -> Optional[str]:
        # Primary: Union Code
        union_code = self._row.get("Union Code")
        if union_code == "LIB":
            return "HR: PULA"

        # Secondary: Sal Plan Descr for DoF staff
        sal_plan_descr = self._row.get("Sal Plan Descr")
        if sal_plan_descr is None:
            print(f"{self.emplid} lacks sufficient data to determine admin group", file=stderr)
            return None

        if sal_plan_descr.startswith("Regular Professional Library"):
            return "DoF: Librarian"
        elif sal_plan_descr.startswith("Reg Prof Specialist"):
            return "DoF: Professional Specialist"
        else:
            return "HR: Non-Bargaining"

    @property
    def is_dof_staff(self) -> bool:
        """Dean of the Faculty staff (Librarians and Professional Specialists)."""
        ag = self.admin_group
        return ag == "DoF: Librarian" or ag == "DoF: Professional Specialist"

    @property
    def phone(self) -> Optional[str]:
        data = self._row.get("OL1 Phone - Phone Number")
        if data:
            local = data.split("/")[1]
            return f"(609) {local}"
        else:
            return None

    @property
    def term_end(self) -> str:
        return self._row.get("Estimated Appt End Date", "")

    @property
    def term_perm(self) -> Optional[str]:
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
    def title(self) -> Optional[str]:
        pref_title = self._row.get("Admin Post Title")
        if pref_title:
            return pref_title
        else:
            return self._row.get("Position - Job Title")

    @property
    def preferred_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def first_name(self) -> str:
        return self._row["Preferred Else Primary First Name"]

    @property
    def last_name(self) -> str:
        return self._row["Preferred Else Primary Last Name"]

    @property
    def email(self) -> str:
        return self._row["E-Mail Address - Campus"]

    @property
    def time(self) -> float:
        return float(self._row["FTE"])

    @property
    def start_date(self) -> str:
        return ReportRow.parse_date(self._row["Hire Date"])

    @property
    def rehire_date(self) -> str:
        return ReportRow.parse_date(self._row["Rehire Date"])

    @property
    def address(self) -> Optional[str]:
        return self.get("Telephone DB Office Location")

    @property
    def position_number(self) -> str:
        # Return actual position number if present
        if self._row.get("Position Number"):
            return self._row["Position Number"]

        # Special cases for staff without position numbers
        if self.is_dof_staff:
            return "[N/A - DoF]"
        elif self.term_perm == "Casual Hourly":
            return "[N/A - Casual]"
        elif "Leave" in self.status:
            return "[N/A]"
        else:
            # Fallback - shouldn't normally reach here
            print(f"{self.emplid} lacks position number and doesn't match known categories", file=stderr)
            return "[N/A]"

    @property
    def grade(self) -> Optional[int]:
        grade_str = self._row.get("Grade")
        if grade_str:
            return int(grade_str)
        return None

    @property
    def division(self) -> str:
        return DIVISION_LOOKUP[self._row["Department Name"]]

    @property
    def ps_department_name(self) -> str:
        return self._row["Department Name"]

    @property
    def ps_department_code(self) -> str:
        return self._row["Dept"]

    @property
    def status(self) -> str:
        return self._row["Status"]

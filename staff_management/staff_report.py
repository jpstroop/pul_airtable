# Standard library imports
from csv import DictReader
from sys import stderr
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

# Local imports
from staff_management.report_row import ReportRow


class StaffReport:
    rows: List[ReportRow]
    filtered_appointments: Dict[str, List[Optional[str]]]  # emplid -> ignored titles

    # Keywords to identify library-related titles (for DoF staff with dual appointments)
    LIBRARY_TITLE_KEYWORDS: List[str] = [
        "Library",
        "Librarian",
        "Curator",
        "Cataloging",
        "Archivist",
        "Archive",
        "Special Collections",
        "Digital Humanities",
    ]

    def __init__(self, file_path: str) -> None:
        self.filtered_appointments: Dict[str, List[Optional[str]]] = {}
        with open(file_path, "r", encoding="utf-16") as f:  # Note encoding
            all_rows = [ReportRow(r) for r in DictReader(f, delimiter="\t")]

        # Filter out duplicate emplids, keeping only library-related titles
        self.rows = self._filter_duplicate_appointments(all_rows)

    def _filter_duplicate_appointments(self, all_rows: List[ReportRow]) -> List[ReportRow]:
        """Filter rows to keep only library-related appointments for DoF staff with dual roles.

        For staff with multiple appointments (same emplid, different titles):
        - Keep the row with a library-related title (contains keywords)
        - If multiple or no library titles found, keep first occurrence
        - Log when duplicates are detected

        Args:
            all_rows: All rows from CSV

        Returns:
            Filtered list with one row per emplid
        """
        # Group rows by emplid
        by_emplid: Dict[str, List[ReportRow]] = {}
        for row in all_rows:
            emplid = row.emplid
            by_emplid.setdefault(emplid, []).append(row)

        filtered: List[ReportRow] = []
        for emplid, rows in by_emplid.items():
            if len(rows) == 1:
                # No duplicates, keep the row
                filtered.append(rows[0])
            else:
                # Multiple appointments - filter by library title
                library_rows = [
                    r for r in rows if self._is_library_title(r.title)
                ]

                if len(library_rows) == 1:
                    # Found one library title, use it
                    chosen = library_rows[0]
                elif len(library_rows) > 1:
                    # Multiple library titles, use first
                    chosen = library_rows[0]
                else:
                    # No library titles found, use first occurrence
                    chosen = rows[0]

                # Store ignored titles; displayed only when a sync change actually occurs
                self.filtered_appointments[emplid] = [r.title for r in rows if r != chosen]
                filtered.append(chosen)

        return filtered

    def _is_library_title(self, title: str) -> bool:
        """Check if a title contains library-related keywords."""
        title_lower = title.lower()
        return any(keyword.lower() in title_lower for keyword in self.LIBRARY_TITLE_KEYWORDS)

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

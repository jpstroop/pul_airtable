# Standard library imports
from typing import Optional

# Local imports
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord
from staff_management.staff_airtable import StaffAirtable


class RecordMatcher:
    """Finds matching Airtable records for CSV report rows.

    Implements 3-tier matching strategy:
    1. Try emplid first (works for everyone)
    2. For DoF staff: fall back to name matching (no position numbers)
    3. For regular staff: fall back to position number matching

    Pure business logic with no side effects - fully testable with mocked StaffAirtable.
    """

    _airtable: StaffAirtable

    def __init__(self, airtable: StaffAirtable) -> None:
        """Initialize RecordMatcher with StaffAirtable instance.

        Args:
            airtable: StaffAirtable instance for looking up records
        """
        self._airtable = airtable

    def find_match(self, report_row: ReportRow) -> tuple[Optional[AirtableRecord], bool]:
        """Find matching Airtable record for a report row.

        Matching strategy:
        - Try emplid first (works for everyone)
        - For DoF staff: fall back to name matching (no position numbers)
        - For regular staff: fall back to position number matching

        Args:
            report_row: CSV row to find matching Airtable record for

        Returns:
            Tuple of (record, should_log) where:
            - record: Matching AirtableRecord if found, None otherwise
            - should_log: True if fallback matching was used (log the update)
        """
        # Try emplid first
        airtable_record = self._airtable.get_record_by_emplid(report_row.emplid)
        should_log = False

        if not airtable_record:
            # Try to find matching record based on staff type
            if report_row.is_dof_staff:
                # DoF staff: match by name (no position numbers)
                airtable_record = self._airtable.get_record_by_name(report_row.preferred_name)
                if airtable_record:
                    should_log = True
            else:
                # Regular staff: match by position number
                position_no = report_row.position_number
                # Skip special [N/A*] position numbers (on leave, DoF, casual)
                if position_no and not position_no.startswith("[N/A"):
                    airtable_record = self._airtable.get_record_by_position_no(position_no)
                    if airtable_record:
                        should_log = True

        return airtable_record, should_log

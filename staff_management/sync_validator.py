# Third party imports
from click import echo
from click import style as click_style

# Local imports
from staff_management.field_mapper import FieldMapper
from staff_management.staff_airtable import StaffAirtable
from staff_management.staff_report import StaffReport


class SyncValidator:
    """Validates and reports discrepancies between CSV and Airtable.

    Consolidates repetitive check logic and centralizes special cases.
    Returns lists for testability, with optional CLI reporting.
    """

    # Special case: Dean position to exclude from "missing from CSV" checks
    DEAN_POSITION: str = "00003305"

    _airtable: StaffAirtable
    _report: StaffReport

    def __init__(self, airtable: StaffAirtable, report: StaffReport) -> None:
        """Initialize SyncValidator with Airtable and report instances.

        Args:
            airtable: StaffAirtable instance for accessing Airtable records
            report: StaffReport instance for accessing CSV data
        """
        self._airtable = airtable
        self._report = report

    def check_emplids_missing_in_airtable(self) -> list[str]:
        """Return emplids in CSV but not in Airtable.

        Returns:
            List of emplids (as strings) that appear in CSV but not Airtable
        """
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._report.all_emplids
        return [eid for eid in report_emplids if eid not in airtable_emplids]

    def check_emplids_missing_in_csv(self) -> list[str]:
        """Return emplids in Airtable but not in CSV.

        Returns:
            List of emplids (as strings) that appear in Airtable but not CSV
        """
        airtable_emplids = self._airtable.all_emplids
        report_emplids = self._report.all_emplids
        return [eid for eid in airtable_emplids if eid not in report_emplids]

    def check_position_numbers_missing_in_airtable(self) -> list[str]:
        """Return position numbers in CSV but not in Airtable.

        Returns:
            List of position numbers that appear in CSV but not Airtable
        """
        airtable_pns = self._airtable.all_position_numbers
        report_pns = self._report.all_position_numbers
        return [pn for pn in report_pns if pn not in airtable_pns]

    def check_position_numbers_missing_in_csv(self) -> list[str]:
        """Return position numbers in Airtable but not in CSV.

        Excludes vacancies and Deans's position.

        Returns:
            List of position numbers that appear in Airtable but not CSV
        """
        airtable_pns = self._airtable.all_position_numbers
        report_pns = self._report.all_position_numbers
        missing = [pn for pn in airtable_pns if pn not in report_pns]

        # Filter out vacancies and the Dean's
        result = []
        for pn in missing:
            if pn == self.DEAN_POSITION:
                continue

            # Check if it's a vacancy
            record = self._airtable.get_record_by_position_no(pn)
            if record:
                fields = FieldMapper.extract_fields(record)
                name = fields.get("pul:Preferred Name")
                if name and str(name).startswith("__VACANCY"):
                    continue

            result.append(pn)

        return result

    def report_discrepancies(self) -> None:
        """Run all checks and echo results to console.

        Uses Click styling for colored output. This method has side effects
        (console output) and is harder to test, but the underlying check methods
        return data and are fully testable.
        """
        # Check emplids missing in Airtable
        missing_in_airtable = self.check_emplids_missing_in_airtable()
        for emplid in missing_in_airtable:
            report_record = self._report.get_record_by_emplid(emplid)
            if report_record is None:
                continue
            name = report_record.get("Name", "Unknown")
            echo(  # pragma: no cover
                click_style(f"Employee {emplid} ({name}) is in CSV but NOT in Airtable", fg="yellow")
            )

        # Check emplids missing in CSV
        missing_in_csv = self.check_emplids_missing_in_csv()
        for emplid in missing_in_csv:
            record = self._airtable.get_record_by_emplid(emplid)
            if record is None:
                continue
            fields = FieldMapper.extract_fields(record)
            name = str(fields.get("pul:Preferred Name", "Unknown"))
            position = str(fields.get("Position Number", ""))
            # Skip Dean position (special case - should remain in Airtable)
            if position == self.DEAN_POSITION:
                continue
            echo(  # pragma: no cover
                click_style(f"Employee {emplid} ({name}) is in Airtable but NOT in CSV Report", fg="yellow")
            )

        # Check position numbers missing in Airtable
        pn_missing_in_airtable = self.check_position_numbers_missing_in_airtable()
        for pn in pn_missing_in_airtable:
            report_row = self._report.get_record_by_position_no(pn)
            if report_row is None:
                continue
            name = report_row.preferred_name
            echo(  # pragma: no cover
                click_style(f"Position Number {pn} ({name}) is missing from Airtable.", fg="yellow")
            )

        # Check position numbers missing in CSV
        pn_missing_in_csv = self.check_position_numbers_missing_in_csv()
        for pn in pn_missing_in_csv:
            record = self._airtable.get_record_by_position_no(pn)
            if record is None:
                continue
            fields = FieldMapper.extract_fields(record)
            name = str(fields.get("pul:Preferred Name", "Unknown"))
            echo(  # pragma: no cover
                click_style(f"Position {pn} ({name}) is in Airtable but NOT in CSV Report", fg="yellow")
            )

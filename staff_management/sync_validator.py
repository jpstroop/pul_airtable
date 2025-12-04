# Standard library imports
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

# Third party imports
from click import echo
from click import style as click_style

# Local imports
from staff_management.field_delta import FieldDelta
from staff_management.field_mapper import FieldMapper
from staff_management.record_matcher import RecordMatcher
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
    _record_matcher: RecordMatcher

    def __init__(self, airtable: StaffAirtable, report: StaffReport) -> None:
        """Initialize SyncValidator with Airtable and report instances.

        Args:
            airtable: StaffAirtable instance for accessing Airtable records
            report: StaffReport instance for accessing CSV data
        """
        self._airtable = airtable
        self._report = report
        self._record_matcher = RecordMatcher(airtable)

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

    def check_field_differences(self) -> List[Tuple[str, Dict[str, Tuple[Any, Any]]]]:
        """Check for field value differences between CSV and Airtable.

        Returns:
            List of tuples: (employee_name, field_delta_dict)
            Only includes records where fields differ between CSV and Airtable.
        """
        differences: List[Tuple[str, Dict[str, Tuple[Any, Any]]]] = []

        for report_row in self._report.rows:
            # Find matching Airtable record
            airtable_record, _ = self._record_matcher.find_match(report_row)
            if not airtable_record:
                continue  # Record doesn't exist in Airtable (covered by other checks)

            # Skip vacancies
            airtable_fields = FieldMapper.extract_fields(airtable_record)
            name = str(airtable_fields.get("pul:Preferred Name", "Unknown"))
            if name.startswith("__VACANCY"):
                continue

            # Compare fields
            new_fields = FieldMapper.map_row_to_fields(report_row)
            delta = FieldDelta.compute_delta(airtable_fields, new_fields)

            if delta:
                differences.append((report_row.preferred_name, delta))

        return differences

    def report_discrepancies(self, verbose: bool = False) -> None:
        """Run all checks and echo results to console.

        Args:
            verbose: If True, show all field changes. If False, show only counts
                    and position number changes (which are critical).

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

        # Check for field value differences in matching records
        field_differences = self.check_field_differences()
        if field_differences:
            if not verbose:
                # Non-verbose: show count and position number changes only
                echo(  # pragma: no cover
                    click_style(
                        f"\nFound {len(field_differences)} record(s) with field differences", fg="cyan", bold=True
                    )
                )
                # Always show position number changes (critical)
                for name, delta in field_differences:
                    if "Position Number" in delta:
                        old_val, new_val = delta["Position Number"]
                        old_str = FieldDelta.format_value(old_val)
                        new_str = FieldDelta.format_value(new_val)
                        echo(  # pragma: no cover
                            click_style(
                                f"{name} [Position Number] changed from [{old_str}] to [{new_str}]", fg="red", bold=True
                            )
                        )
            else:
                # Verbose: show all field changes
                echo(  # pragma: no cover
                    click_style(f"\nField differences between CSV and Airtable:", fg="cyan", bold=True)
                )
                for name, delta in field_differences:
                    FieldDelta.display_changes(name, delta)

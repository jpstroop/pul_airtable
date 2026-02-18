# Standard library imports
from json import load
from sys import exit as sys_exit
from sys import stderr
from sys import stdout
from time import sleep
from typing import List
from typing import Optional
from typing import TextIO
from typing import cast

# Third party imports
from click import echo
from click import style as click_style
from pyairtable.api.types import Fields

# Local imports
from staff_management.field_delta import FieldDelta
from staff_management.field_mapper import FieldMapper
from staff_management.record_matcher import RecordMatcher
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord
from staff_management.staff_airtable import JSONDict
from staff_management.staff_airtable import JSONType
from staff_management.staff_airtable import StaffAirtable
from staff_management.staff_report import StaffReport
from staff_management.sync_prompts import MissingFromCSVAction
from staff_management.sync_prompts import SyncPrompts
from staff_management.sync_validator import SyncValidator

THROTTLE_INTERVAL: float = 0.2
MANUALLY_MANAGED_STATUSES: frozenset[str] = frozenset({"Resigned/End date approaching"})


class App:
    _airtable: StaffAirtable
    _staff_report: StaffReport
    _record_matcher: RecordMatcher
    _sync_validator: SyncValidator
    _verbose: bool

    def __init__(self, src_data_path: str, config: Optional[JSONDict] = None, verbose: bool = False) -> None:
        if config is None:
            # Legacy: load from private.json (for backward compatibility)
            config = App._load_private()

        self._airtable = StaffAirtable(
            str(config["PAT"]),
            str(config["BASE_ID"]),
            str(config["ALL_STAFF_TABLE_ID"]),
            str(config["REMOVAL_TABLE_ID"]),
        )
        self._staff_report = StaffReport(src_data_path)
        self._record_matcher = RecordMatcher(self._airtable)
        self._sync_validator = SyncValidator(self._airtable, self._staff_report)
        self._verbose = verbose

    def _handle_position_number_change(
        self, report_row: ReportRow, airtable_record: AirtableRecord, data: Fields
    ) -> tuple[bool, bool]:
        """Handle position number changes with user prompts.

        Returns:
            Tuple of (should_continue, already_updated)
            - (True, False): No change, continue with normal update
            - (True, True): Handled and updated, skip normal update
            - (False, _): Abort sync
        """
        fields = FieldMapper.extract_fields(airtable_record)

        if report_row.position_number == fields["Position Number"]:
            return True, False  # No change, continue with normal update

        # Check if this is just correcting [N/A] to proper format ([N/A - DoF] or [N/A - Casual])
        old_pos = fields["Position Number"]
        new_pos = report_row.position_number
        if old_pos == "[N/A]" and new_pos in ("[N/A - DoF]", "[N/A - Casual]"):
            # Just a correction - update without prompting
            data["Position Number"] = new_pos
            self._airtable.update_record(str(airtable_record["id"]), data, log=True)
            return True, True  # Continue, but already updated

        # Real position number change - requires manual intervention
        emplid = report_row.emplid
        preferred_name = fields["pul:Preferred Name"]
        SyncPrompts.show_position_change_error(
            preferred_name=str(preferred_name),
            emplid=emplid,
            old_position=str(fields["Position Number"]),
            new_position=report_row.position_number,
        )
        sys_exit(1)
        return False, False  # unreachable but type-safe

    def _handle_new_staff_member(self, report_row: ReportRow) -> None:
        """Handle new staff members not found in Airtable.

        Different handling for DoF staff vs regular staff:
        - DoF staff: prompt user (new position or vacancy replacement)
        - Casual staff: skip
        - Staff on leave ([N/A]): note but skip
        - Regular staff with position numbers: add automatically
        """
        if report_row.is_dof_staff:
            # Interactive prompt for new DoF staff
            is_new_position = SyncPrompts.prompt_new_dof_staff(report_row)
            if not is_new_position:
                return  # User wants to handle manually

            # It's a new position, create it
            data = FieldMapper.map_row_to_fields(report_row)
            self._airtable.add_new_record(data)
            sleep(THROTTLE_INTERVAL)

        elif report_row.position_number == "[N/A - Casual]":
            # Casual staff without matches are skipped
            SyncPrompts.show_casual_staff_skipped(report_row.preferred_name, report_row.emplid)

        elif report_row.position_number == "[N/A]":
            # Staff on leave without position numbers
            SyncPrompts.show_staff_on_leave(report_row.last_name)

        else:
            # Regular staff with position numbers - check if position exists
            position_no = report_row.position_number
            existing_position = self._airtable.get_record_by_position_no(position_no)

            should_add = SyncPrompts.prompt_new_regular_staff(report_row, existing_position)
            if should_add:
                data = FieldMapper.map_row_to_fields(report_row)
                self._airtable.add_new_record(data)
                sleep(THROTTLE_INTERVAL)

    def _handle_missing_from_csv(self, emplid: str) -> bool:
        """Handle Airtable records not found in CSV report.

        Prompts user with 5 options:
        1. Remove and create vacancy (employee left)
        2. Remove without creating vacancy (casual/eliminated position)
        3. Mark as on leave
        4. Ignore and continue (skip)
        5. Abort sync

        Returns:
            True if sync should continue, False if sync should abort
        """
        record = self._airtable.get_record_by_emplid(emplid)
        if record is None:
            return True  # Continue if record not found

        fields = FieldMapper.extract_fields(record)
        name = str(fields.get("pul:Preferred Name", "Unknown"))
        position = str(fields.get("Position Number", ""))

        # Skip Dean position (special case - should remain in Airtable)
        if position == "00003305":
            return True

        # Prompt user for action
        on_leave_status = bool(fields.get("pul:On Leave?", False))
        action = SyncPrompts.prompt_missing_from_csv(
            name=name,
            emplid=emplid,
            title=str(fields.get("Title", "")),
            netid=str(fields.get("netid", "")),
            position=str(fields.get("Position Number", "")),
            on_leave=on_leave_status,
        )

        # Handle user's choice
        if action == MissingFromCSVAction.CONVERT_TO_VACANCY:
            SyncPrompts.show_converting_to_vacancy(name)
            self._airtable.employee_to_vacancy(emplid)
            sleep(THROTTLE_INTERVAL)
            return True
        elif action == MissingFromCSVAction.DELETE_WITHOUT_VACANCY:
            SyncPrompts.show_deleting_record(name)
            self._airtable.delete_record(str(record["id"]))
            sleep(THROTTLE_INTERVAL)
            return True
        elif action == MissingFromCSVAction.MARK_ON_LEAVE:
            SyncPrompts.show_marking_on_leave(name)
            leave_data = cast(Fields, {"pul:On Leave?": True})
            self._airtable.update_record(str(record["id"]), leave_data)
            sleep(THROTTLE_INTERVAL)
            return True
        elif action == MissingFromCSVAction.SKIP:
            SyncPrompts.show_skipping_manual_handling(name)
            return True
        elif action == MissingFromCSVAction.ABORT:
            SyncPrompts.show_sync_aborted()
            return False
        else:
            # Shouldn't reach here, but handle gracefully
            SyncPrompts.show_skipping_manual_handling(name)
            return True

    @property
    def all_vacancies(self) -> List[AirtableRecord]:
        return self._airtable.all_vacancies

    def sync_airtable_with_report(self) -> None:
        """Sync CSV report data to Airtable.

        Matching strategy:
        - Try emplid first (works for everyone)
        - For DoF staff: fall back to name matching (no position numbers)
        - For regular staff: fall back to position number matching

        CLI decision points (Phase 5):
        - DoF staff with no emplid or name match: new position or replacing vacancy?
        - Position number changed: person on leave or changed positions?
        - Record missing from CSV: person left or on leave?
        """
        for r in self._staff_report.rows:
            airtable_record, log = self._record_matcher.find_match(r)

            if airtable_record:
                fields = FieldMapper.extract_fields(airtable_record)
                data = FieldMapper.map_row_to_fields(r)
                if str(fields["pul:Preferred Name"]).startswith("__VACANCY"):
                    data = FieldMapper.map_row_to_fields(r)

                # Preserve manually managed search statuses
                existing_status = fields.get("pul:Search Status")
                if isinstance(existing_status, str) and existing_status in MANUALLY_MANAGED_STATUSES:
                    data["pul:Search Status"] = existing_status

                # Check for position number changes
                should_continue, already_updated = self._handle_position_number_change(r, airtable_record, data)
                if not should_continue:
                    return  # Abort sync

                # Only update if not already handled by position number change logic
                if not already_updated:
                    is_filtered = r.emplid in self._staff_report.filtered_appointments
                    if self._verbose or is_filtered:
                        delta = FieldDelta.compute_delta(fields, data)
                        if self._verbose and delta:
                            FieldDelta.display_changes(r.preferred_name, delta)
                        if is_filtered and "Title" in delta:
                            ignored = self._staff_report.filtered_appointments[r.emplid]
                            ignored_str = ", ".join(f"'{t}'" for t in ignored if t)
                            echo(click_style(
                                f"Note: {r.preferred_name} has multiple appointments; using '{r.title}', ignoring: {ignored_str}",
                                fg="cyan",
                            ))

                    if fields["Position Number"] != "[N/A]":
                        self._airtable.update_record(str(airtable_record["id"]), data, log=log)
                    else:
                        echo(click_style(f"FYI: {r.last_name} position number is [N/A]", fg="cyan"))  # pragma: no cover
            else:
                # No matching record found - this is a NEW person/position
                self._handle_new_staff_member(r)

        # Phase 2: Check for Airtable records missing from CSV
        echo(  # pragma: no cover
            click_style("\nChecking for Airtable records not in CSV report...", fg="cyan", bold=True)
        )
        missing_from_report = self._sync_validator.check_emplids_missing_in_csv()

        for emplid in missing_from_report:
            if not self._handle_missing_from_csv(emplid):
                sys_exit(0)  # User chose to abort

        echo(click_style("\n✓ Sync complete", fg="green", bold=True))  # pragma: no cover

    def update_supervisor_info(self) -> None:
        # 1: Clear all
        # 2. Update supervisor hierarchy (uses CSV report)
        # 3. Update pula managers (uses Airtable)
        # 4. Update DoF managers (uses Airtable)
        self._airtable.clear_supervisor_statuses()
        self._airtable.update_supervisor_hierarchy(self._staff_report, THROTTLE_INTERVAL, self._verbose)
        self._airtable.update_pula_supervisor_statuses()
        self._airtable.update_dof_librarian_supervisor_statuses()

    def employee_to_vacancy(self, emplid: str) -> None:
        self._airtable.employee_to_vacancy(emplid)

    def run_checks(self) -> None:
        """Run validation checks and report discrepancies between CSV and Airtable."""
        self._sync_validator.report_discrepancies(verbose=self._verbose)

    @staticmethod
    def _load_private(pth: str = "./private.json") -> JSONDict:
        with open(pth, "r") as f:
            result = load(f)
            return cast(JSONDict, result)


def print_json(json_payload: JSONType, f: TextIO = stdout) -> None:
    # For debugging
    # Standard library imports
    from json import dumps

    print(dumps(json_payload, ensure_ascii=False, indent=2), file=f)

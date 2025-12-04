# Standard library imports
from enum import Enum
from typing import Optional

# Third party imports
from click import confirm
from click import echo
from click import prompt
from click import style as click_style

# Local imports
from staff_management.field_mapper import FieldMapper
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord


class MissingFromCSVAction(Enum):
    """Actions for handling Airtable records missing from CSV."""

    CONVERT_TO_VACANCY = 1
    DELETE_WITHOUT_VACANCY = 2
    MARK_ON_LEAVE = 3
    SKIP = 4
    ABORT = 5


class SyncPrompts:
    """Handles all user interaction prompts during sync operations.

    Centralizes CLI user interaction logic for testability and separation of concerns.
    All methods are static since no state is needed.
    """

    @staticmethod
    def show_position_change_error(preferred_name: str, emplid: str, old_position: str, new_position: str) -> None:
        """Display error message for real position number changes.

        Real position number changes require manual intervention before sync can continue.

        Args:
            preferred_name: Employee's preferred name
            emplid: Employee ID
            old_position: Current position number in Airtable
            new_position: New position number from CSV
        """
        echo(click_style(f"\nPosition number changed for {preferred_name} (emplid {emplid})", fg="red", bold=True))
        echo(f"  Airtable: {old_position}")
        echo(f"  CSV:      {new_position}")
        echo(
            click_style(
                f"\nThis person changed positions. Please convert to vacancy in old position first.", fg="yellow"
            )
        )
        echo(f"  Then re-run sync.")

    @staticmethod
    def prompt_new_dof_staff(report_row: ReportRow) -> bool:
        """Prompt user about new DoF staff member.

        Returns:
            True if user confirms this is a NEW position (should be created),
            False if replacing vacancy (user should update manually)
        """
        echo(
            click_style(f"\n{report_row.preferred_name} (DoF staff) - No matching record found", fg="yellow", bold=True)
        )
        echo(f"  Title: {report_row.title}")
        echo(f"  NetID: {report_row.get('Net ID')}")
        echo(f"  Emplid: {report_row.emplid}")

        if not confirm("Is this a NEW position (vs replacing an existing vacancy)?", default=False):
            # TODO: Show list of vacancies and let user select which one to update
            echo(
                click_style(
                    "Skipping - please update Airtable manually to match this person to a vacancy.", fg="yellow"
                )
            )
            return False

        return True  # User confirmed it's a new position

    @staticmethod
    def show_casual_staff_skipped(preferred_name: str, emplid: str) -> None:
        """Display message that casual staff member is being skipped.

        Args:
            preferred_name: Employee's preferred name
            emplid: Employee ID
        """
        echo(click_style(f"Skipping casual hourly staff: {preferred_name} ({emplid})", fg="cyan"))

    @staticmethod
    def show_staff_on_leave(last_name: str) -> None:
        """Display info message that staff member's position is [N/A].

        Args:
            last_name: Employee's last name
        """
        echo(click_style(f"FYI: {last_name} position number is [N/A]", fg="cyan"))

    @staticmethod
    def prompt_new_regular_staff(report_row: ReportRow, existing_position: Optional[AirtableRecord]) -> bool:
        """Prompt user about new regular staff member.

        Args:
            report_row: CSV row data for the new staff member
            existing_position: Existing Airtable record with same position number (if any)

        Returns:
            True if user confirms adding to Airtable, False to skip
        """
        position_no = report_row.position_number

        echo(click_style(f"\n{report_row.preferred_name} - No matching record found", fg="yellow", bold=True))
        echo(f"  Title: {report_row.title}")
        echo(f"  NetID: {report_row.get('Net ID')}")
        echo(f"  Emplid: {report_row.emplid}")
        echo(f"  Position: {position_no}")

        if existing_position:
            # Position number exists - likely a vacancy
            existing_fields = FieldMapper.extract_fields(existing_position)
            vacancy_name = existing_fields.get("pul:Preferred Name", "")
            if str(vacancy_name).startswith("__VACANCY"):
                echo(click_style(f"  → This position number exists as a VACANCY: {vacancy_name}", fg="cyan"))
            else:
                echo(click_style(f"  → This position number already exists for: {vacancy_name}", fg="red"))
        else:
            # New position number
            echo(click_style(f"  → This is a NEW position number", fg="magenta", bold=True))

        if confirm("Add this person to Airtable?", default=True):
            return True
        else:
            echo(click_style("Skipped - handle manually", fg="yellow"))
            return False

    @staticmethod
    def prompt_missing_from_csv(
        name: str, emplid: str, title: str, netid: str, position: str, on_leave: bool
    ) -> MissingFromCSVAction:
        """Prompt user about Airtable record missing from CSV.

        Args:
            name: Employee's preferred name
            emplid: Employee ID
            title: Job title
            netid: Network ID
            position: Position number
            on_leave: Whether currently marked as on leave

        Returns:
            User's chosen action
        """
        leave_indicator = " [CURRENTLY MARKED AS ON LEAVE]" if on_leave else ""

        echo(
            click_style(
                f"\n{name} (emplid {emplid}) is in Airtable but NOT in CSV report{leave_indicator}",
                fg="yellow",
                bold=True,
            )
        )
        echo(f"  Title: {title}")
        echo(f"  NetID: {netid}")
        echo(f"  Position: {position}")

        choice = prompt(
            "Action",
            type=int,
            default=4,
            show_choices=True,
            show_default=True,
            prompt_suffix=":\n  [1] Remove and create vacancy\n  [2] Remove without vacancy (casual/eliminated)\n  [3] Mark as on leave\n  [4] Ignore and continue\n  [5] Abort sync\nChoice: ",
        )

        try:
            return MissingFromCSVAction(choice)
        except ValueError:
            echo(click_style(f"Invalid choice {choice}, defaulting to SKIP", fg="red"))
            return MissingFromCSVAction.SKIP

    @staticmethod
    def show_converting_to_vacancy(name: str) -> None:
        """Display message about converting employee to vacancy."""
        echo(click_style(f"Converting {name} to vacancy...", fg="yellow"))

    @staticmethod
    def show_deleting_record(name: str) -> None:
        """Display message about deleting record."""
        echo(click_style(f"Deleting {name} from Airtable...", fg="yellow"))

    @staticmethod
    def show_marking_on_leave(name: str) -> None:
        """Display message about marking employee as on leave."""
        echo(click_style(f"Marking {name} as on leave...", fg="cyan"))

    @staticmethod
    def show_skipping_manual_handling(name: str) -> None:
        """Display message about skipping for manual handling."""
        echo(click_style(f"Skipping {name} - handle manually", fg="yellow"))

    @staticmethod
    def show_sync_aborted() -> None:
        """Display message that sync was aborted by user."""
        echo(click_style("\nSync aborted by user", fg="red", bold=True))

"""Tests for App class helper methods."""

# Standard library imports
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

# Local imports
from main import App
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord


class TestHandlePositionNumberChange:
    """Tests for App._handle_position_number_change()"""

    def test_no_change_continues(self, sample_pula_staff_row: dict[str, str]) -> None:
        """Should return (True, False) when position number hasn't changed."""
        # Third party imports
        from pyairtable.api.types import Fields

        # Local imports
        from main import App

        mock_airtable_record = cast(
            AirtableRecord,
            {"id": "rec123", "fields": {"Position Number": "00012345", "pul:Preferred Name": "John Smith"}},
        )

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)

            row = ReportRow(sample_pula_staff_row)
            data = cast(Fields, {"Position Number": "00012345"})

            should_continue, already_updated = (
                app._handle_position_number_change(  # pyright: ignore[reportPrivateUsage]
                    row, mock_airtable_record, data
                )
            )

            assert should_continue is True
            assert already_updated is False

    def test_na_to_na_dof_correction_automatic(self, sample_dof_librarian_row: dict[str, str]) -> None:
        """Should automatically update [N/A] to [N/A - DoF] and return (True, True)."""
        # Third party imports
        from pyairtable.api.types import Fields

        # Local imports
        from main import App

        mock_airtable_record = cast(
            AirtableRecord, {"id": "rec123", "fields": {"Position Number": "[N/A]", "pul:Preferred Name": "Jordan Lee"}}
        )

        mock_airtable = Mock()

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            row = ReportRow(sample_dof_librarian_row)
            data = cast(Fields, {"Position Number": "[N/A - DoF]"})

            should_continue, already_updated = (
                app._handle_position_number_change(  # pyright: ignore[reportPrivateUsage]
                    row, mock_airtable_record, data
                )
            )

            assert should_continue is True
            assert already_updated is True  # Record was updated automatically
            assert data["Position Number"] == "[N/A - DoF]"
            mock_airtable.update_record.assert_called_once_with("rec123", data, log=True)

    @patch("main.sys_exit")
    @patch("main.echo")
    def test_real_position_change_aborts(
        self, mock_echo: MagicMock, mock_sys_exit: MagicMock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Real position number changes should abort sync and require manual intervention."""
        # Third party imports
        from pyairtable.api.types import Fields

        # Local imports
        from main import App

        mock_airtable_record = cast(
            AirtableRecord,
            {"id": "rec123", "fields": {"Position Number": "00012345", "pul:Preferred Name": "John Smith"}},
        )

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)

            row = ReportRow(sample_pula_staff_row)
            row._row["Position Number"] = "00099999"  # Different position
            data = cast(Fields, {"Position Number": "00099999"})

            app._handle_position_number_change(row, mock_airtable_record, data)  # pyright: ignore[reportPrivateUsage]

            # Should call sys_exit(1) for real position changes
            mock_sys_exit.assert_called_once_with(1)


class TestHandleNewStaffMember:
    """Tests for App._handle_new_staff_member()"""

    def test_casual_staff_skipped(self, sample_casual_row: dict[str, str]) -> None:
        """Casual staff without matches should be skipped."""
        # Local imports
        from main import App

        mock_airtable = Mock()

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            row = ReportRow(sample_casual_row)
            app._handle_new_staff_member(row)  # pyright: ignore[reportPrivateUsage]

            # Should not add any record
            mock_airtable.add_new_record.assert_not_called()

    @patch("staff_management.sync_prompts.SyncPrompts.prompt_new_regular_staff")
    @patch("main.sleep")
    def test_regular_staff_added_automatically(
        self, mock_sleep: MagicMock, mock_prompt: MagicMock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Regular staff with position numbers should prompt and be added when confirmed."""
        # Third party imports
        from pyairtable.api.types import Fields

        # Local imports
        from main import App
        from staff_management.field_mapper import FieldMapper

        mock_prompt.return_value = True  # User confirms adding the person
        mock_airtable = Mock()
        mock_airtable.get_record_by_position_no.return_value = None  # Position doesn't exist

        with patch.object(App, "__init__", lambda x, y, z: None):
            with patch.object(FieldMapper, "map_row_to_fields") as mock_map:
                mock_map.return_value = cast(Fields, {"test": "data"})

                app = App("dummy", None)
                app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

                row = ReportRow(sample_pula_staff_row)
                app._handle_new_staff_member(row)  # pyright: ignore[reportPrivateUsage]

                mock_airtable.add_new_record.assert_called_once()
                mock_sleep.assert_called_once()
                mock_prompt.assert_called_once()


class TestHandleMissingFromCSV:
    """Tests for App._handle_missing_from_csv()"""

    def test_dean_position_skipped(self) -> None:
        """Dean position should be automatically skipped."""
        # Local imports
        from main import App

        mock_airtable = Mock()
        dean_record = cast(
            AirtableRecord,
            {
                "id": "recDean",
                "fields": {"pul:Preferred Name": "Dean", "University ID": "999999999", "Position Number": "00003305"},
            },
        )
        mock_airtable.get_record_by_emplid.return_value = dean_record

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            result = app._handle_missing_from_csv("999999999")  # pyright: ignore[reportPrivateUsage]

            assert result is True  # Should continue
            mock_airtable.employee_to_vacancy.assert_not_called()

    @patch("staff_management.sync_prompts.SyncPrompts.prompt_missing_from_csv")
    @patch("main.sleep")
    def test_convert_to_vacancy(self, mock_sleep: MagicMock, mock_prompt: MagicMock) -> None:
        """Should convert to vacancy when user chooses option 1."""
        # Local imports
        from main import App
        from staff_management.sync_prompts import MissingFromCSVAction

        mock_prompt.return_value = MissingFromCSVAction.CONVERT_TO_VACANCY

        mock_airtable = Mock()
        test_record = cast(
            AirtableRecord,
            {
                "id": "rec123",
                "fields": {
                    "pul:Preferred Name": "Test Person",
                    "University ID": "123456789",
                    "Position Number": "00012345",
                    "Title": "Test Title",
                },
            },
        )
        mock_airtable.get_record_by_emplid.return_value = test_record

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            result = app._handle_missing_from_csv("123456789")  # pyright: ignore[reportPrivateUsage]

            assert result is True
            mock_airtable.employee_to_vacancy.assert_called_once_with("123456789")
            mock_sleep.assert_called_once()

    @patch("staff_management.sync_prompts.SyncPrompts.prompt_missing_from_csv")
    @patch("main.sleep")
    def test_delete_without_vacancy(self, mock_sleep: MagicMock, mock_prompt: MagicMock) -> None:
        """Should delete record without vacancy when user chooses option 2."""
        # Local imports
        from main import App
        from staff_management.sync_prompts import MissingFromCSVAction

        mock_prompt.return_value = MissingFromCSVAction.DELETE_WITHOUT_VACANCY

        mock_airtable = Mock()
        test_record = cast(
            AirtableRecord,
            {
                "id": "rec123",
                "fields": {
                    "pul:Preferred Name": "Test Person",
                    "University ID": "123456789",
                    "Position Number": "00012345",
                    "Title": "Test Title",
                },
            },
        )
        mock_airtable.get_record_by_emplid.return_value = test_record

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            result = app._handle_missing_from_csv("123456789")  # pyright: ignore[reportPrivateUsage]

            assert result is True
            mock_airtable.delete_record.assert_called_once_with("rec123")
            mock_sleep.assert_called_once()

    @patch("staff_management.sync_prompts.SyncPrompts.prompt_missing_from_csv")
    @patch("main.sleep")
    def test_mark_as_on_leave(self, mock_sleep: MagicMock, mock_prompt: MagicMock) -> None:
        """Should mark record as on leave when user chooses option 3."""
        # Local imports
        from main import App
        from staff_management.sync_prompts import MissingFromCSVAction

        mock_prompt.return_value = MissingFromCSVAction.MARK_ON_LEAVE

        mock_airtable = Mock()
        test_record = cast(
            AirtableRecord,
            {
                "id": "rec123",
                "fields": {
                    "pul:Preferred Name": "Test Person",
                    "University ID": "123456789",
                    "Position Number": "00012345",
                    "Title": "Test Title",
                },
            },
        )
        mock_airtable.get_record_by_emplid.return_value = test_record

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            result = app._handle_missing_from_csv("123456789")  # pyright: ignore[reportPrivateUsage]
            assert result is True
            mock_airtable.update_record.assert_called_once()
            # Check that it was called with the on leave flag
            call_args = mock_airtable.update_record.call_args
            assert call_args[0][0] == "rec123"  # record_id
            assert call_args[0][1]["pul:On Leave?"] is True  # data
            mock_sleep.assert_called_once()

    @patch("staff_management.sync_prompts.SyncPrompts.prompt_missing_from_csv")
    def test_abort_sync(self, mock_prompt: MagicMock) -> None:
        """Should return False when user chooses to abort."""
        # Local imports
        from main import App
        from staff_management.sync_prompts import MissingFromCSVAction

        mock_prompt.return_value = MissingFromCSVAction.ABORT

        mock_airtable = Mock()
        test_record = cast(
            AirtableRecord,
            {
                "id": "rec123",
                "fields": {
                    "pul:Preferred Name": "Test Person",
                    "University ID": "123456789",
                    "Position Number": "00012345",
                    "Title": "Test Title",
                },
            },
        )
        mock_airtable.get_record_by_emplid.return_value = test_record

        with patch.object(App, "__init__", lambda x, y, z: None):
            app = App("dummy", None)
            app._airtable = mock_airtable  # pyright: ignore[reportPrivateUsage]

            result = app._handle_missing_from_csv("123456789")  # pyright: ignore[reportPrivateUsage]

            assert result is False  # Should abort


class TestSyncAirtableWithReportIntegration:
    """Integration tests for sync_airtable_with_report() orchestration.

    These tests would require complex setup with mock Airtable, StaffReport,
    and all helper classes. Deferred until integration test scaffolding is established.
    """

    def test_syncs_existing_records_with_updates(self) -> None:
        """Should update existing Airtable records with CSV data.

        Integration test covering:
        - Loop through report rows
        - Match existing records
        - Update records with new data
        - Handle logging appropriately
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

    def test_handles_vacancy_replacement(self) -> None:
        """Should replace vacancy records with new employees.

        Integration test covering:
        - Detect vacancy records
        - Replace with actual employee data
        - Preserve position information
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

    def test_detects_and_logs_leave_status_changes(self) -> None:
        """Should detect and log when employees go on leave or return.

        Integration test covering:
        - Compare old vs new on-leave status
        - Log status changes with appropriate messages
        - Continue processing after logging
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

    def test_handles_position_na_special_case(self) -> None:
        """Should handle [N/A] position numbers appropriately.

        Integration test covering:
        - Detect [N/A] position numbers
        - Skip update but log message
        - Continue processing other records
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

    def test_processes_missing_from_csv_phase(self) -> None:
        """Should check for Airtable records not in CSV and handle them.

        Integration test covering:
        - Run validator check for missing emplids
        - Handle each missing record appropriately
        - Allow abort if user chooses
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

    def test_completes_full_sync_successfully(self) -> None:
        """Should complete full sync process end-to-end.

        Integration test covering:
        - Process all CSV rows
        - Update existing records
        - Add new records
        - Handle missing records
        - Display completion message
        """
        # Third party imports
        from pytest import skip

        skip("Integration test - requires full mock setup")

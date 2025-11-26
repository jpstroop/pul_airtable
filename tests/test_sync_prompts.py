# Standard library imports
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

# Third party imports
from pytest import fixture

# Local imports
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord
from staff_management.sync_prompts import MissingFromCSVAction
from staff_management.sync_prompts import SyncPrompts


@fixture
def sample_dof_row() -> dict[str, str]:
    """Sample DoF staff member row data."""
    return {
        "Emplid": "987654321",
        "Preferred Else Primary First Name": "Jordan",
        "Preferred Else Primary Last Name": "Lee",
        "E-Mail Address - Campus": "jlee@princeton.edu",
        "Net ID": "jlee",
        "Sal Plan Descr": "Reg Prof Specialist",
        "Sal Plan": "PS",
        "Department Name": "Library-Dean's Office",
        "Dept": "31000",
        "Position - Job Title": "Director of Basketweaving",
        "FTE": "1.0",
        "Hire Date": "1/1/2015",
        "Rehire Date": "1/1/2015",
        "Status": "Active",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "888888888",
    }


@fixture
def sample_regular_row() -> dict[str, str]:
    """Sample regular staff member row data."""
    return {
        "Emplid": "123456789",
        "Preferred Else Primary First Name": "John",
        "Preferred Else Primary Last Name": "Smith",
        "E-Mail Address - Campus": "jsmith@princeton.edu",
        "Net ID": "jsmith",
        "Position Number": "00012345",
        "Union Code": "LIB",
        "Sal Plan Descr": "Library Support Staff",
        "Sal Plan": "LS",
        "Department Name": "Lib-IT & Digital Initiatives",
        "Dept": "31600",
        "Position - Job Title": "Software Developer",
        "Grade": "10",
        "FTE": "1.0",
        "Hire Date": "6/1/2019",
        "Rehire Date": "6/1/2019",
        "Status": "Active",
        "Staff": "Regular",
        "Manager/Supervisor Emplid": "999999999",
    }


@fixture
def sample_casual_row() -> dict[str, str]:
    """Sample casual staff member row data."""
    return {
        "Emplid": "111222333",
        "Preferred Else Primary First Name": "Jane",
        "Preferred Else Primary Last Name": "Casual",
        "E-Mail Address - Campus": "jcasual@princeton.edu",
        "Net ID": "jcasual",
        "Sal Plan Descr": "Casual Hourly",
        "Sal Plan": "CH",
        "Department Name": "Lib-Collections & Access Svcs",
        "Dept": "31200",
        "Position - Job Title": "Hourly Worker",
        "FTE": "0.2",
        "Hire Date": "9/1/2023",
        "Rehire Date": "9/1/2023",
        "Status": "Active",
        "Staff": "Casual Hourly",
        "Manager/Supervisor Emplid": "999999999",
    }


class TestShowPositionChangeError:
    """Tests for show_position_change_error()"""

    @patch("staff_management.sync_prompts.echo")
    def test_displays_error_message(self, mock_echo: MagicMock) -> None:
        """Should display formatted error message with position details."""
        SyncPrompts.show_position_change_error(
            preferred_name="John Smith", emplid="123456789", old_position="00012345", new_position="00099999"
        )

        # Should call echo multiple times
        assert mock_echo.call_count >= 4

        # Check that important info is in the calls
        all_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "John Smith" in all_calls
        assert "123456789" in all_calls
        assert "00012345" in all_calls
        assert "00099999" in all_calls


class TestPromptNewDofStaff:
    """Tests for prompt_new_dof_staff()"""

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_true_when_user_confirms_new_position(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_dof_row: dict[str, str]
    ) -> None:
        """Should return True when user confirms it's a new position."""
        mock_confirm.return_value = True

        row = ReportRow(sample_dof_row)
        result = SyncPrompts.prompt_new_dof_staff(row)

        assert result is True
        mock_confirm.assert_called_once()
        # Should display info about the person
        assert mock_echo.call_count >= 4

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_false_when_user_denies_new_position(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_dof_row: dict[str, str]
    ) -> None:
        """Should return False when user says it's not a new position."""
        mock_confirm.return_value = False

        row = ReportRow(sample_dof_row)
        result = SyncPrompts.prompt_new_dof_staff(row)

        assert result is False
        mock_confirm.assert_called_once()


class TestShowCasualStaffSkipped:
    """Tests for show_casual_staff_skipped()"""

    @patch("staff_management.sync_prompts.echo")
    def test_displays_skipped_message(self, mock_echo: MagicMock) -> None:
        """Should display message about skipping casual staff."""
        SyncPrompts.show_casual_staff_skipped("Jane Casual", "111222333")

        mock_echo.assert_called_once()
        call_text = str(mock_echo.call_args)
        assert "Jane Casual" in call_text
        assert "111222333" in call_text
        assert "casual" in call_text.lower()


class TestShowStaffOnLeave:
    """Tests for show_staff_on_leave()"""

    @patch("staff_management.sync_prompts.echo")
    def test_displays_on_leave_message(self, mock_echo: MagicMock) -> None:
        """Should display FYI message about [N/A] position."""
        SyncPrompts.show_staff_on_leave("Smith")

        mock_echo.assert_called_once()
        call_text = str(mock_echo.call_args)
        assert "Smith" in call_text
        assert "[N/A]" in call_text


class TestPromptNewRegularStaff:
    """Tests for prompt_new_regular_staff()"""

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_true_when_user_confirms(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_regular_row: dict[str, str]
    ) -> None:
        """Should return True when user confirms adding person."""
        mock_confirm.return_value = True

        row = ReportRow(sample_regular_row)
        result = SyncPrompts.prompt_new_regular_staff(row, None)

        assert result is True
        mock_confirm.assert_called_once()

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_false_when_user_denies(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_regular_row: dict[str, str]
    ) -> None:
        """Should return False when user denies adding person."""
        mock_confirm.return_value = False

        row = ReportRow(sample_regular_row)
        result = SyncPrompts.prompt_new_regular_staff(row, None)

        assert result is False
        mock_confirm.assert_called_once()

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_shows_vacancy_when_position_exists(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_regular_row: dict[str, str]
    ) -> None:
        """Should show vacancy info when position already exists."""
        mock_confirm.return_value = True

        existing = cast(
            AirtableRecord,
            {"id": "rec123", "fields": {"Position Number": "00012345", "pul:Preferred Name": "__VACANCY_001__"}},
        )

        row = ReportRow(sample_regular_row)
        result = SyncPrompts.prompt_new_regular_staff(row, existing)

        assert result is True
        # Should mention vacancy
        all_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "VACANCY" in all_calls

    @patch("staff_management.sync_prompts.confirm")
    @patch("staff_management.sync_prompts.echo")
    def test_shows_new_position_when_no_existing(
        self, mock_echo: MagicMock, mock_confirm: MagicMock, sample_regular_row: dict[str, str]
    ) -> None:
        """Should indicate new position when no existing record."""
        mock_confirm.return_value = True

        row = ReportRow(sample_regular_row)
        result = SyncPrompts.prompt_new_regular_staff(row, None)

        assert result is True
        # Should mention new position
        all_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "NEW position" in all_calls


class TestPromptMissingFromCSV:
    """Tests for prompt_missing_from_csv()"""

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_convert_to_vacancy_for_choice_1(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return CONVERT_TO_VACANCY when user chooses 1."""
        mock_prompt.return_value = 1

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.CONVERT_TO_VACANCY

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_delete_for_choice_2(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return DELETE_WITHOUT_VACANCY when user chooses 2."""
        mock_prompt.return_value = 2

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.DELETE_WITHOUT_VACANCY

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_mark_on_leave_for_choice_3(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return MARK_ON_LEAVE when user chooses 3."""
        mock_prompt.return_value = 3

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.MARK_ON_LEAVE

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_skip_for_choice_4(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return SKIP when user chooses 4."""
        mock_prompt.return_value = 4

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.SKIP

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_abort_for_choice_5(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return ABORT when user chooses 5."""
        mock_prompt.return_value = 5

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.ABORT

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_returns_skip_for_invalid_choice(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should return SKIP for invalid choices."""
        mock_prompt.return_value = 99  # Invalid choice

        result = SyncPrompts.prompt_missing_from_csv(
            name="John Smith",
            emplid="123456789",
            title="Developer",
            netid="jsmith",
            position="00012345",
            on_leave=False,
        )

        assert result == MissingFromCSVAction.SKIP

    @patch("staff_management.sync_prompts.prompt")
    @patch("staff_management.sync_prompts.echo")
    def test_shows_on_leave_indicator_when_on_leave(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        """Should show [ON LEAVE] indicator when person is on leave."""
        mock_prompt.return_value = 4

        SyncPrompts.prompt_missing_from_csv(
            name="John Smith", emplid="123456789", title="Developer", netid="jsmith", position="00012345", on_leave=True
        )

        # Check that ON LEAVE appears in the output
        all_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "ON LEAVE" in all_calls


class TestShowMethods:
    """Tests for simple show_* methods that just display messages."""

    @patch("staff_management.sync_prompts.echo")
    def test_show_converting_to_vacancy(self, mock_echo: MagicMock) -> None:
        """Should display converting to vacancy message."""
        SyncPrompts.show_converting_to_vacancy("John Smith")
        mock_echo.assert_called_once()
        assert "John Smith" in str(mock_echo.call_args)
        assert "vacancy" in str(mock_echo.call_args).lower()

    @patch("staff_management.sync_prompts.echo")
    def test_show_deleting_record(self, mock_echo: MagicMock) -> None:
        """Should display deleting record message."""
        SyncPrompts.show_deleting_record("John Smith")
        mock_echo.assert_called_once()
        assert "John Smith" in str(mock_echo.call_args)
        assert "Deleting" in str(mock_echo.call_args)

    @patch("staff_management.sync_prompts.echo")
    def test_show_marking_on_leave(self, mock_echo: MagicMock) -> None:
        """Should display marking on leave message."""
        SyncPrompts.show_marking_on_leave("John Smith")
        mock_echo.assert_called_once()
        assert "John Smith" in str(mock_echo.call_args)
        assert "on leave" in str(mock_echo.call_args).lower()

    @patch("staff_management.sync_prompts.echo")
    def test_show_skipping_manual_handling(self, mock_echo: MagicMock) -> None:
        """Should display skipping for manual handling message."""
        SyncPrompts.show_skipping_manual_handling("John Smith")
        mock_echo.assert_called_once()
        assert "John Smith" in str(mock_echo.call_args)
        assert "Skipping" in str(mock_echo.call_args)

    @patch("staff_management.sync_prompts.echo")
    def test_show_sync_aborted(self, mock_echo: MagicMock) -> None:
        """Should display sync aborted message."""
        SyncPrompts.show_sync_aborted()
        mock_echo.assert_called_once()
        call_text = str(mock_echo.call_args)
        assert "aborted" in call_text.lower()

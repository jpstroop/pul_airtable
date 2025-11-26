# Standard library imports
from typing import cast
from unittest.mock import Mock

# Third party imports
from pytest import fixture

# Local imports
from staff_management.record_matcher import RecordMatcher
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord


@fixture
def mock_airtable() -> Mock:
    """Create a mock StaffAirtable instance."""
    return Mock()


@fixture
def record_matcher(mock_airtable: Mock) -> RecordMatcher:
    """Create a RecordMatcher with mocked StaffAirtable."""
    return RecordMatcher(mock_airtable)


class TestFindMatchByEmplid:
    """Tests for matching by emplid (first tier)"""

    def test_finds_record_by_emplid(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Should find record by emplid and return should_log=False."""
        mock_record = cast(AirtableRecord, {"id": "rec123", "fields": {"University ID": "123456789"}})
        mock_airtable.get_record_by_emplid.return_value = mock_record

        row = ReportRow(sample_pula_staff_row)
        record, should_log = record_matcher.find_match(row)

        assert record == mock_record
        assert should_log is False
        mock_airtable.get_record_by_emplid.assert_called_once_with("123456789")

    def test_emplid_match_skips_fallback_lookups(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """When emplid matches, should not attempt name or position lookups."""
        mock_record = cast(AirtableRecord, {"id": "rec123", "fields": {"University ID": "123456789"}})
        mock_airtable.get_record_by_emplid.return_value = mock_record

        row = ReportRow(sample_pula_staff_row)
        record_matcher.find_match(row)

        # Should only call emplid lookup
        mock_airtable.get_record_by_emplid.assert_called_once()
        mock_airtable.get_record_by_name.assert_not_called()
        mock_airtable.get_record_by_position_no.assert_not_called()


class TestFindMatchDofStaffByName:
    """Tests for DoF staff fallback to name matching (second tier)"""

    def test_dof_staff_falls_back_to_name_when_emplid_missing(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_dof_librarian_row: dict[str, str]
    ) -> None:
        """DoF staff without emplid match should match by name."""
        mock_record = cast(AirtableRecord, {"id": "rec456", "fields": {"pul:Preferred Name": "Jordan Lee"}})
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_name.return_value = mock_record

        row = ReportRow(sample_dof_librarian_row)
        record, should_log = record_matcher.find_match(row)

        assert record == mock_record
        assert should_log is True  # Fallback matching should be logged
        mock_airtable.get_record_by_name.assert_called_once_with("Jordan Lee")

    def test_dof_staff_without_matches_returns_none(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_dof_librarian_row: dict[str, str]
    ) -> None:
        """DoF staff with no emplid or name match should return None."""
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_name.return_value = None

        row = ReportRow(sample_dof_librarian_row)
        record, should_log = record_matcher.find_match(row)

        assert record is None
        assert should_log is False

    def test_dof_staff_does_not_check_position_number(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_dof_librarian_row: dict[str, str]
    ) -> None:
        """DoF staff should never attempt position number matching."""
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_name.return_value = None

        row = ReportRow(sample_dof_librarian_row)
        record_matcher.find_match(row)

        mock_airtable.get_record_by_position_no.assert_not_called()


class TestFindMatchRegularStaffByPositionNumber:
    """Tests for regular staff fallback to position number matching (third tier)"""

    def test_regular_staff_falls_back_to_position_number(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Regular staff without emplid match should match by position number."""
        mock_record = cast(AirtableRecord, {"id": "rec789", "fields": {"Position Number": "00012345"}})
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_position_no.return_value = mock_record

        row = ReportRow(sample_pula_staff_row)
        record, should_log = record_matcher.find_match(row)

        assert record == mock_record
        assert should_log is True  # Fallback matching should be logged
        mock_airtable.get_record_by_position_no.assert_called_once_with("00012345")

    def test_regular_staff_without_matches_returns_none(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Regular staff with no emplid or position match should return None."""
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_position_no.return_value = None

        row = ReportRow(sample_pula_staff_row)
        record, should_log = record_matcher.find_match(row)

        assert record is None
        assert should_log is False

    def test_regular_staff_does_not_check_name(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Regular staff should never attempt name matching."""
        mock_airtable.get_record_by_emplid.return_value = None
        mock_airtable.get_record_by_position_no.return_value = None

        row = ReportRow(sample_pula_staff_row)
        record_matcher.find_match(row)

        mock_airtable.get_record_by_name.assert_not_called()

    def test_skips_position_lookup_for_na_position(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_on_leave_row: dict[str, str]
    ) -> None:
        """Staff with '[N/A]' position should not attempt position lookup."""
        # Modify fixture to have [N/A] position
        sample_on_leave_row["Position Number"] = ""  # Will result in [N/A]

        mock_airtable.get_record_by_emplid.return_value = None

        row = ReportRow(sample_on_leave_row)
        record, should_log = record_matcher.find_match(row)

        assert record is None
        assert should_log is False
        mock_airtable.get_record_by_position_no.assert_not_called()


class TestMatchingPriority:
    """Tests for matching priority and tier ordering"""

    def test_emplid_takes_priority_over_name(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_dof_librarian_row: dict[str, str]
    ) -> None:
        """Emplid match should be used even if name also matches."""
        emplid_record = cast(AirtableRecord, {"id": "rec_emplid", "fields": {"University ID": "234567890"}})
        name_record = cast(AirtableRecord, {"id": "rec_name", "fields": {"pul:Preferred Name": "Jordan Lee"}})

        mock_airtable.get_record_by_emplid.return_value = emplid_record
        mock_airtable.get_record_by_name.return_value = name_record

        row = ReportRow(sample_dof_librarian_row)
        record, should_log = record_matcher.find_match(row)

        # Should return emplid match, not name match
        assert record == emplid_record
        assert record["id"] == "rec_emplid"
        assert should_log is False

    def test_emplid_takes_priority_over_position(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_pula_staff_row: dict[str, str]
    ) -> None:
        """Emplid match should be used even if position also matches."""
        emplid_record = cast(AirtableRecord, {"id": "rec_emplid", "fields": {"University ID": "123456789"}})
        position_record = cast(AirtableRecord, {"id": "rec_position", "fields": {"Position Number": "00012345"}})

        mock_airtable.get_record_by_emplid.return_value = emplid_record
        mock_airtable.get_record_by_position_no.return_value = position_record

        row = ReportRow(sample_pula_staff_row)
        record, should_log = record_matcher.find_match(row)

        # Should return emplid match, not position match
        assert record == emplid_record
        assert record["id"] == "rec_emplid"
        assert should_log is False


class TestCasualStaff:
    """Tests for casual staff with special position numbers"""

    def test_casual_staff_skips_position_lookup(
        self, record_matcher: RecordMatcher, mock_airtable: Mock, sample_casual_row: dict[str, str]
    ) -> None:
        """Casual staff with [N/A - Casual] should not attempt position lookup."""
        mock_airtable.get_record_by_emplid.return_value = None

        row = ReportRow(sample_casual_row)
        record, should_log = record_matcher.find_match(row)

        assert record is None
        assert should_log is False
        mock_airtable.get_record_by_position_no.assert_not_called()

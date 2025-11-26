# Standard library imports
from typing import cast
from unittest.mock import Mock

# Third party imports
from pytest import fixture

# Local imports
from staff_management.staff_airtable import AirtableRecord
from staff_management.sync_validator import SyncValidator


@fixture
def mock_airtable() -> Mock:
    """Create a mock StaffAirtable instance."""
    return Mock()


@fixture
def mock_report() -> Mock:
    """Create a mock StaffReport instance."""
    return Mock()


@fixture
def sync_validator(mock_airtable: Mock, mock_report: Mock) -> SyncValidator:
    """Create a SyncValidator with mocked dependencies."""
    return SyncValidator(mock_airtable, mock_report)


class TestSpecialCases:
    """Tests for special case constants"""

    def test_dean_position_constant(self) -> None:
        """DEAN_POSITION should be set correctly."""
        assert SyncValidator.DEAN_POSITION == "00003305"


class TestCheckEmplidsMissingInAirtable:
    """Tests for check_emplids_missing_in_airtable()"""

    def test_returns_empty_when_all_in_airtable(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return empty list when all CSV emplids exist in Airtable."""
        mock_airtable.all_emplids = ["123", "456", "789"]
        mock_report.all_emplids = ["123", "456", "789"]

        result = sync_validator.check_emplids_missing_in_airtable()

        assert result == []

    def test_returns_missing_emplids(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return emplids that are in CSV but not Airtable."""
        mock_airtable.all_emplids = ["123", "456"]
        mock_report.all_emplids = ["123", "456", "789", "999"]

        result = sync_validator.check_emplids_missing_in_airtable()

        assert set(result) == {"789", "999"}

    def test_handles_empty_airtable(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return all CSV emplids when Airtable is empty."""
        mock_airtable.all_emplids = []
        mock_report.all_emplids = ["123", "456"]

        result = sync_validator.check_emplids_missing_in_airtable()

        assert set(result) == {"123", "456"}


class TestCheckEmplidsMissingInCSV:
    """Tests for check_emplids_missing_in_csv()"""

    def test_returns_empty_when_all_in_csv(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return empty list when all Airtable emplids exist in CSV."""
        mock_airtable.all_emplids = ["123", "456"]
        mock_report.all_emplids = ["123", "456", "789"]

        result = sync_validator.check_emplids_missing_in_csv()

        assert result == []

    def test_returns_missing_emplids(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return emplids that are in Airtable but not CSV."""
        mock_airtable.all_emplids = ["123", "456", "789"]
        mock_report.all_emplids = ["123"]

        result = sync_validator.check_emplids_missing_in_csv()

        assert set(result) == {"456", "789"}


class TestCheckPositionNumbersMissingInAirtable:
    """Tests for check_position_numbers_missing_in_airtable()"""

    def test_returns_empty_when_all_in_airtable(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return empty list when all CSV positions exist in Airtable."""
        mock_airtable.all_position_numbers = ["00012345", "00067890"]
        mock_report.all_position_numbers = ["00012345", "00067890"]

        result = sync_validator.check_position_numbers_missing_in_airtable()

        assert result == []

    def test_returns_missing_positions(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return positions that are in CSV but not Airtable."""
        mock_airtable.all_position_numbers = ["00012345"]
        mock_report.all_position_numbers = ["00012345", "00067890", "00099999"]

        result = sync_validator.check_position_numbers_missing_in_airtable()

        assert set(result) == {"00067890", "00099999"}


class TestCheckPositionNumbersMissingInCSV:
    """Tests for check_position_numbers_missing_in_csv()"""

    def test_returns_empty_when_all_in_csv(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return empty list when all Airtable positions exist in CSV."""
        mock_airtable.all_position_numbers = ["00012345"]
        mock_report.all_position_numbers = ["00012345", "00067890"]

        result = sync_validator.check_position_numbers_missing_in_csv()

        assert result == []

    def test_returns_missing_positions(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should return positions that are in Airtable but not CSV."""
        mock_airtable.all_position_numbers = ["00012345", "00067890", "00099999"]
        mock_report.all_position_numbers = ["00012345"]

        # Mock records for non-vacancy positions
        mock_airtable.get_record_by_position_no.return_value = cast(
            AirtableRecord, {"id": "rec123", "fields": {"pul:Preferred Name": "Regular Employee"}}
        )

        result = sync_validator.check_position_numbers_missing_in_csv()

        assert set(result) == {"00067890", "00099999"}

    def test_excludes_dean_position(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should exclude Dean position (00003305) from results."""
        mock_airtable.all_position_numbers = ["00012345", "00003305"]
        mock_report.all_position_numbers = []

        # Mock record for regular position
        mock_airtable.get_record_by_position_no.return_value = cast(
            AirtableRecord, {"id": "rec123", "fields": {"pul:Preferred Name": "Regular Employee"}}
        )

        result = sync_validator.check_position_numbers_missing_in_csv()

        # Dean position should be excluded
        assert "00003305" not in result
        assert set(result) == {"00012345"}

    def test_excludes_vacancies(self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock) -> None:
        """Should exclude vacancies from results."""
        mock_airtable.all_position_numbers = ["00012345", "00067890"]
        mock_report.all_position_numbers = []

        def mock_get_record(pn: str) -> AirtableRecord:
            if pn == "00012345":
                return cast(AirtableRecord, {"id": "rec1", "fields": {"pul:Preferred Name": "Regular Employee"}})
            else:  # 00067890 is a vacancy
                return cast(AirtableRecord, {"id": "rec2", "fields": {"pul:Preferred Name": "__VACANCY_001__"}})

        mock_airtable.get_record_by_position_no.side_effect = mock_get_record

        result = sync_validator.check_position_numbers_missing_in_csv()

        # Vacancy should be excluded
        assert "00067890" not in result
        assert result == ["00012345"]

    def test_handles_none_record(self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock) -> None:
        """Should handle when get_record_by_position_no returns None."""
        mock_airtable.all_position_numbers = ["00012345"]
        mock_report.all_position_numbers = []
        mock_airtable.get_record_by_position_no.return_value = None

        result = sync_validator.check_position_numbers_missing_in_csv()

        # Should include position even if record is None (shouldn't crash)
        assert result == ["00012345"]


class TestReportDiscrepancies:
    """Tests for report_discrepancies()"""

    def test_runs_without_error(self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock) -> None:
        """Should run without errors when there are no discrepancies."""
        mock_airtable.all_emplids = ["123"]
        mock_report.all_emplids = ["123"]
        mock_airtable.all_position_numbers = ["00012345"]
        mock_report.all_position_numbers = ["00012345"]

        # Should not raise
        sync_validator.report_discrepancies()

    def test_handles_discrepancies(self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock) -> None:
        """Should handle reporting when discrepancies exist."""
        mock_airtable.all_emplids = ["123", "456"]
        mock_report.all_emplids = ["123", "789"]
        mock_airtable.all_position_numbers = []
        mock_report.all_position_numbers = []

        # Mock lookups
        mock_report.get_record_by_emplid.return_value = {"Name": "Test Employee"}
        mock_airtable.get_record_by_emplid.return_value = cast(
            AirtableRecord, {"id": "rec1", "fields": {"pul:Preferred Name": "Test"}}
        )

        # Should not raise
        sync_validator.report_discrepancies()

    def test_skips_when_report_record_is_none(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should skip emplids in CSV when report record is None."""
        mock_airtable.all_emplids = []
        mock_report.all_emplids = ["999"]
        mock_airtable.all_position_numbers = []
        mock_report.all_position_numbers = []

        # Return None for the lookup
        mock_report.get_record_by_emplid.return_value = None

        # Should not raise or print anything
        sync_validator.report_discrepancies()

    def test_skips_when_airtable_record_is_none(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should skip emplids in Airtable when record is None."""
        mock_airtable.all_emplids = ["999"]
        mock_report.all_emplids = []
        mock_airtable.all_position_numbers = []
        mock_report.all_position_numbers = []

        # Return None for the lookup
        mock_airtable.get_record_by_emplid.return_value = None

        # Should not raise or print anything
        sync_validator.report_discrepancies()

    def test_skips_dean_position_in_emplid_check(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should skip Dean position when checking emplids missing in CSV."""
        mock_airtable.all_emplids = ["999999999"]
        mock_report.all_emplids = []
        mock_airtable.all_position_numbers = []
        mock_report.all_position_numbers = []

        # Dean record with position 00003305
        mock_airtable.get_record_by_emplid.return_value = cast(
            AirtableRecord, {"id": "recDean", "fields": {"pul:Preferred Name": "Dean", "Position Number": "00003305"}}
        )

        # Should not print anything for Dean position
        sync_validator.report_discrepancies()

    def test_skips_when_position_report_row_is_none(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should skip position numbers when report row is None."""
        mock_airtable.all_emplids = []
        mock_report.all_emplids = []
        mock_airtable.all_position_numbers = []
        mock_report.all_position_numbers = ["00099999"]

        # Return None for position lookup
        mock_report.get_record_by_position_no.return_value = None

        # Should not raise or print anything
        sync_validator.report_discrepancies()

    def test_skips_when_position_airtable_record_is_none(
        self, sync_validator: SyncValidator, mock_airtable: Mock, mock_report: Mock
    ) -> None:
        """Should skip position numbers when Airtable record is None."""
        mock_airtable.all_emplids = []
        mock_report.all_emplids = []
        mock_airtable.all_position_numbers = ["00099999"]
        mock_report.all_position_numbers = []

        # Return None for position lookup
        mock_airtable.get_record_by_position_no.return_value = None

        # Should not raise or print anything
        sync_validator.report_discrepancies()

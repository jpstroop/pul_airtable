# Standard library imports
from io import StringIO
from typing import cast
from unittest.mock import patch

# Third party imports
from pytest import fixture
from pytest import raises

# Local imports
from staff_management.field_mapper import FieldMapper
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord


@fixture
def sample_airtable_record() -> AirtableRecord:
    """Sample Airtable record for testing."""
    return cast(
        AirtableRecord,
        {
            "id": "rec123",
            "fields": {
                "University ID": "123456789",
                "pul:Preferred Name": "Alex Smith",
                "Title": "Librarian",
                "Position Number": "00012345",
            },
        },
    )


@fixture
def sample_report_row(sample_pula_staff_row: dict[str, str]) -> ReportRow:
    """Sample ReportRow for testing - uses PULA staff fixture."""
    return ReportRow(sample_pula_staff_row)


@fixture
def leave_report_row(sample_on_leave_row: dict[str, str]) -> ReportRow:
    """Sample ReportRow for staff on leave - uses on-leave fixture."""
    return ReportRow(sample_on_leave_row)


class TestExtractFields:
    """Tests for FieldMapper.extract_fields()"""

    def test_extract_fields_returns_fields_dict(self, sample_airtable_record: AirtableRecord) -> None:
        """Test that extract_fields returns the fields dictionary."""
        result = FieldMapper.extract_fields(sample_airtable_record)
        assert result == sample_airtable_record["fields"]

    def test_extract_fields_has_correct_keys(self, sample_airtable_record: AirtableRecord) -> None:
        """Test that extracted fields contain expected keys."""
        result = FieldMapper.extract_fields(sample_airtable_record)
        assert "University ID" in result
        assert "pul:Preferred Name" in result
        assert "Title" in result
        assert "Position Number" in result

    def test_extract_fields_type_narrowing(self, sample_airtable_record: AirtableRecord) -> None:
        """Test that extract_fields returns JSONDict type."""
        result = FieldMapper.extract_fields(sample_airtable_record)
        # The function should cast to JSONDict
        assert isinstance(result, dict)


class TestMapRowToFields:
    """Tests for FieldMapper.map_row_to_fields()"""

    def test_maps_all_required_fields(self, sample_report_row: ReportRow) -> None:
        """Test that all required Airtable fields are mapped."""
        result = FieldMapper.map_row_to_fields(sample_report_row)

        # Verify all expected fields are present
        assert "University ID" in result
        assert "Division" in result
        assert "Admin. Group" in result
        assert "pul:Search Status" in result
        assert "University Phone" in result
        assert "End Date" in result
        assert "Term/Perm/CA Track" in result
        assert "Title" in result
        assert "pul:Preferred Name" in result
        assert "Email" in result
        assert "Last Name" in result
        assert "First Name" in result
        assert "Time" in result
        assert "Start Date" in result
        assert "Rehire Date" in result
        assert "Grade" in result
        assert "Sal. Plan" in result
        assert "Position Number" in result
        assert "Address" in result
        assert "netid" in result
        assert "PS Department Name" in result
        assert "PS Department Code" in result
        assert "pul:On Leave?" in result

    def test_maps_emplid_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that emplid is mapped to 'University ID'."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["University ID"] == "123456789"

    def test_maps_name_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that name fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["pul:Preferred Name"] == "Alex Smith"
        assert result["First Name"] == "Alex"
        assert result["Last Name"] == "Smith"

    def test_maps_contact_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that contact fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["Email"] == "asmith@princeton.edu"
        assert result["netid"] == "asmith"
        # sample_pula_staff_row doesn't have phone or address in conftest
        # These may be empty/missing in actual data

    def test_maps_position_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that position-related fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["Title"] == "Library Assistant"
        assert result["Position Number"] == "00012345"
        assert result["Division"] == "Collections and Access Services"
        assert result["Admin. Group"] == "HR: PULA"

    def test_maps_employment_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that employment fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["Time"] == 1.0  # FTE is a float
        assert result["Grade"] == 7  # Grade is an int
        assert result["Sal. Plan"] == "LS"
        # Term/Perm/CA Track depends on Staff field which varies by fixture

    def test_maps_date_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that date fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["Start Date"] == "2020-01-15"
        assert result["Rehire Date"] == "2020-01-15"
        # No end date in fixture

    def test_maps_department_fields_correctly(self, sample_report_row: ReportRow) -> None:
        """Test that department fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["PS Department Code"] == "31200"
        # sample_pula_staff_row doesn't have PS Department Name

    def test_sets_search_status_to_hired(self, sample_report_row: ReportRow) -> None:
        """Test that 'pul:Search Status' is always set to 'Hired'."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["pul:Search Status"] == "Hired"

    def test_on_leave_false_for_active_staff(self, sample_report_row: ReportRow) -> None:
        """Test that 'pul:On Leave?' is False for active staff."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert result["pul:On Leave?"] is False

    def test_on_leave_true_for_leave_with_pay(self, leave_report_row: ReportRow) -> None:
        """Test that 'pul:On Leave?' is True for 'Leave With Pay' status."""
        result = FieldMapper.map_row_to_fields(leave_report_row)
        assert result["pul:On Leave?"] is True

    def test_handles_exception_with_emplid_logging(self, sample_pula_staff_row: dict[str, str]) -> None:
        """Test that exceptions are logged with emplid and re-raised."""
        # Create a ReportRow that will raise an exception when accessing a property
        row = ReportRow(sample_pula_staff_row)

        # Patch a property to raise an exception
        with patch.object(type(row), "emplid", new_callable=lambda: property(lambda self: "999999999")):
            with patch.object(
                type(row),
                "division",
                new_callable=lambda: property(lambda self: (_ for _ in ()).throw(ValueError("Test error"))),
            ):
                # Capture stderr
                captured_stderr = StringIO()
                with patch("staff_management.field_mapper.stderr", captured_stderr):
                    with raises(ValueError, match="Test error"):
                        FieldMapper.map_row_to_fields(row)

                    # Verify emplid was logged to stderr
                    stderr_output = captured_stderr.getvalue()
                    assert "999999999" in stderr_output
                    assert "Error with emplid" in stderr_output

    def test_maps_hr_staff_correctly(self, leave_report_row: ReportRow) -> None:
        """Test that HR staff (PULA) fields are mapped correctly."""
        result = FieldMapper.map_row_to_fields(leave_report_row)
        assert result["Admin. Group"] == "HR: PULA"
        assert result["Division"] == "ReCAP"

    def test_maps_dof_staff_correctly(self, sample_dof_librarian_row: dict[str, str]) -> None:
        """Test that DoF staff fields are mapped correctly."""
        row = ReportRow(sample_dof_librarian_row)
        result = FieldMapper.map_row_to_fields(row)
        assert result["Admin. Group"] == "DoF: Librarian"
        assert result["Division"] == "Data, Research, and Teaching Services"

    def test_result_is_fields_type(self, sample_report_row: ReportRow) -> None:
        """Test that result is of type Fields (dictionary)."""
        result = FieldMapper.map_row_to_fields(sample_report_row)
        assert isinstance(result, dict)

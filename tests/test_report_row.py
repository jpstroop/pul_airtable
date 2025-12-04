# Standard library imports
from typing import Dict

# Third party imports
import pytest

# Local imports
from staff_management.report_row import ReportRow


def test_report_row_basic_properties(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test basic property access for a PULA staff member."""
    row = ReportRow(sample_pula_staff_row)

    assert row.emplid == "123456789"
    assert row.first_name == "Alex"
    assert row.last_name == "Smith"
    assert row.preferred_name == "Alex Smith"
    assert row.email == "asmith@princeton.edu"
    assert row["Net ID"] == "asmith"


def test_admin_group_pula(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test admin group determination for PULA staff."""
    row = ReportRow(sample_pula_staff_row)
    assert row.admin_group == "HR: PULA"
    assert not row.is_dof_staff


def test_admin_group_dof_librarian(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test admin group determination for DoF Librarian."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.admin_group == "DoF: Librarian"
    assert row.is_dof_staff


def test_admin_group_dof_specialist(sample_dof_specialist_row: Dict[str, str]) -> None:
    """Test admin group determination for DoF Professional Specialist."""
    row = ReportRow(sample_dof_specialist_row)
    assert row.admin_group == "DoF: Professional Specialist"
    assert row.is_dof_staff


def test_position_number_regular(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test position number for regular staff with position number."""
    row = ReportRow(sample_pula_staff_row)
    assert row.position_number == "00012345"


def test_position_number_dof(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test position number for DoF staff without position number."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.position_number == "[N/A - DoF]"


def test_position_number_casual(sample_casual_row: Dict[str, str]) -> None:
    """Test position number for casual hourly staff."""
    row = ReportRow(sample_casual_row)
    assert row.position_number == "[N/A - Casual]"


def test_position_number_on_leave(sample_on_leave_row: Dict[str, str]) -> None:
    """Test position number for staff on leave with position number."""
    row = ReportRow(sample_on_leave_row)
    # When staff have a position number, it's returned even if on leave
    assert row.position_number == "00054321"


def test_term_perm_permanent(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test term/perm determination for permanent staff."""
    row = ReportRow(sample_pula_staff_row)
    assert row.term_perm == "Permanent"


def test_term_perm_casual(sample_casual_row: Dict[str, str]) -> None:
    """Test term/perm determination for casual hourly."""
    row = ReportRow(sample_casual_row)
    assert row.term_perm == "Casual Hourly"


def test_division_lookup(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test division name mapping."""
    row = ReportRow(sample_pula_staff_row)
    assert row.division == "Collections and Access Services"


def test_grade_present(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test grade parsing when present."""
    row = ReportRow(sample_pula_staff_row)
    assert row.grade == 7


def test_grade_absent(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test grade when absent."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.grade is None


def test_time_fte(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test FTE parsing."""
    row = ReportRow(sample_pula_staff_row)
    assert row.time == 1.0


def test_supervisor_emplid(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test supervisor emplid parsing."""
    row = ReportRow(sample_pula_staff_row)
    assert row.super_emplid == "987654321"


def test_title_admin_post(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test title uses Admin Post Title when available."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.title == "Data Services Librarian"


def test_title_position_job(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test title falls back to Position - Job Title."""
    row = ReportRow(sample_pula_staff_row)
    assert row.title == "Library Assistant"


class TestParseDateStaticMethod:
    """Tests for ReportRow.parse_date() static method."""

    def test_parse_date_with_slash_format(self) -> None:
        """Test parsing date with '/' format (e.g., '1/15/2020 12:00:00 AM')."""
        result = ReportRow.parse_date("1/15/2020 12:00:00 AM")
        assert result == "2020-01-15"

    def test_parse_date_with_iso_format(self) -> None:
        """Test parsing date with ISO format (e.g., '2020-01-15')."""
        result = ReportRow.parse_date("2020-01-15")
        assert result == "2020-01-15"

    def test_parse_date_with_iso_format_and_time(self) -> None:
        """Test parsing date with ISO format and time (e.g., '2020-01-15 10:30:00')."""
        result = ReportRow.parse_date("2020-01-15 10:30:00")
        assert result == "2020-01-15"

    def test_parse_date_single_digit_month_day(self) -> None:
        """Test parsing date with single digit month and day."""
        result = ReportRow.parse_date("5/3/2019 12:00:00 AM")
        assert result == "2019-05-03"


class TestPhoneProperty:
    """Tests for phone property formatting."""

    def test_phone_with_valid_data(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test phone formatting with valid data."""
        sample_pula_staff_row["OL1 Phone - Phone Number"] = "123/45678"
        row = ReportRow(sample_pula_staff_row)
        assert row.phone == "(609) 45678"

    def test_phone_with_missing_data(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test phone returns None when data is missing."""
        sample_pula_staff_row.pop("OL1 Phone - Phone Number", None)
        row = ReportRow(sample_pula_staff_row)
        assert row.phone is None


class TestTermPermEdgeCases:
    """Tests for term_perm property edge cases."""

    def test_ca_track_with_end_date_and_lr_sal_plan(self, sample_dof_librarian_row: Dict[str, str]) -> None:
        """Test CA Track determination (has end date AND Sal Plan = LR)."""
        sample_dof_librarian_row["Estimated Appt End Date"] = "12/31/2025 12:00:00 AM"
        sample_dof_librarian_row["Sal Plan"] = "LR"
        row = ReportRow(sample_dof_librarian_row)
        assert row.term_perm == "CA Track"

    def test_term_with_end_date_but_not_lr(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test Term determination (has end date but NOT LR sal plan)."""
        sample_pula_staff_row["Estimated Appt End Date"] = "6/30/2024 12:00:00 AM"
        row = ReportRow(sample_pula_staff_row)
        assert row.term_perm == "Term"

    def test_term_perm_missing_sal_plan(
        self, sample_pula_staff_row: Dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test term_perm returns None when Sal Plan is missing."""
        sample_pula_staff_row.pop("Sal Plan")
        row = ReportRow(sample_pula_staff_row)
        result = row.term_perm

        assert result is None
        captured = capsys.readouterr()
        # This prints to stdout, not stderr (line 107 in report_row.py)
        assert "lacks a Sal Plan" in captured.out


class TestAdminGroupEdgeCases:
    """Tests for admin_group property edge cases."""

    def test_admin_group_non_bargaining(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test admin group determination for Non-Bargaining staff."""
        sample_pula_staff_row.pop("Union Code")  # Remove union code
        sample_pula_staff_row["Sal Plan Descr"] = "Executive Staff"
        row = ReportRow(sample_pula_staff_row)
        assert row.admin_group == "HR: Non-Bargaining"
        assert not row.is_dof_staff

    def test_admin_group_missing_sal_plan_descr(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test admin group returns None when Sal Plan Descr is missing."""
        sample_pula_staff_row.pop("Union Code")  # Remove union code
        sample_pula_staff_row.pop("Sal Plan Descr")  # Remove sal plan descr
        row = ReportRow(sample_pula_staff_row)
        result = row.admin_group

        # Should return None and print warning to stderr
        assert result is None


class TestDateProperties:
    """Tests for date properties (start_date, rehire_date)."""

    def test_start_date_slash_format(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test start_date with slash format."""
        row = ReportRow(sample_pula_staff_row)
        assert row.start_date == "2020-01-15"

    def test_rehire_date_slash_format(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test rehire_date with slash format."""
        row = ReportRow(sample_pula_staff_row)
        assert row.rehire_date == "2020-01-15"

    def test_start_date_iso_format(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test start_date with ISO format."""
        sample_pula_staff_row["Hire Date"] = "2020-01-15"
        row = ReportRow(sample_pula_staff_row)
        assert row.start_date == "2020-01-15"


class TestAddressAndDepartmentProperties:
    """Tests for address, department, and status properties."""

    def test_address_present(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test address property when present."""
        sample_pula_staff_row["Telephone DB Office Location"] = "Firestone Library, Room 123"
        row = ReportRow(sample_pula_staff_row)
        assert row.address == "Firestone Library, Room 123"

    def test_address_missing(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test address property returns None when missing."""
        sample_pula_staff_row.pop("Telephone DB Office Location", None)
        row = ReportRow(sample_pula_staff_row)
        assert row.address is None

    def test_ps_department_name(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test ps_department_name property."""
        row = ReportRow(sample_pula_staff_row)
        assert row.ps_department_name == "Lib-Collections & Access Svcs"

    def test_ps_department_code(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test ps_department_code property."""
        row = ReportRow(sample_pula_staff_row)
        assert row.ps_department_code == "31200"

    def test_status(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test status property."""
        row = ReportRow(sample_pula_staff_row)
        assert row.status == "Active"


class TestConstructorWhitespaceHandling:
    """Tests for constructor whitespace stripping."""

    def test_strips_whitespace_from_values(self) -> None:
        """Test that constructor strips whitespace from all values."""
        row_data = {
            "Emplid": "  123456789  ",
            "Preferred Else Primary First Name": " Alex ",
            "Preferred Else Primary Last Name": "Smith  ",
        }
        row = ReportRow(row_data)
        assert row.emplid == "123456789"
        assert row.first_name == "Alex"
        assert row.last_name == "Smith"

    def test_empty_strings_not_added_to_row(self) -> None:
        """Test that empty strings (after strip) are not added to internal dict."""
        row_data = {
            "Emplid": "123456789",
            "Preferred Else Primary First Name": "Alex",
            "Preferred Else Primary Last Name": "Smith",
            "E-Mail Address - Campus": "asmith@princeton.edu",
            "Grade": "   ",  # Whitespace only
            "Union Code": "",  # Empty string
        }
        row = ReportRow(row_data)

        # These should return None via .get() since they were empty
        assert row.get("Grade") is None
        assert row.get("Union Code") is None


class TestDivisionLookupError:
    """Tests for division lookup error handling."""

    def test_division_lookup_unknown_department(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test that unknown department raises KeyError."""
        sample_pula_staff_row["Department Name"] = "Unknown Department"
        row = ReportRow(sample_pula_staff_row)

        with pytest.raises(KeyError):
            _ = row.division


class TestSupervisorEmplidEdgeCases:
    """Tests for supervisor emplid edge cases."""

    def test_super_emplid_none_when_missing(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test super_emplid returns None when supervisor is missing."""
        sample_pula_staff_row.pop("Manager/Supervisor Emplid")
        row = ReportRow(sample_pula_staff_row)
        assert row.super_emplid is None

    def test_super_emplid_zero_padded(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test super_emplid is zero-padded to 9 digits."""
        sample_pula_staff_row["Manager/Supervisor Emplid"] = "123"
        row = ReportRow(sample_pula_staff_row)
        assert row.super_emplid == "000000123"


class TestPositionNumberEdgeCases:
    """Tests for position_number edge cases."""

    def test_position_number_with_leave_status(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test position number returns [N/A] when Status contains 'Leave' and no position number."""
        sample_pula_staff_row.pop("Position Number")
        sample_pula_staff_row.pop("Union Code")  # Make non-PULA
        sample_pula_staff_row["Sal Plan Descr"] = "Executive Staff"  # Non-Bargaining
        sample_pula_staff_row["Status"] = "Leave Without Pay"
        sample_pula_staff_row["Staff"] = "Regular"  # Not casual
        row = ReportRow(sample_pula_staff_row)
        assert row.position_number == "[N/A]"

    def test_position_number_fallback_case(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test position number fallback when no category matches."""
        sample_pula_staff_row.pop("Position Number")
        sample_pula_staff_row.pop("Union Code")  # Make non-PULA
        sample_pula_staff_row["Sal Plan Descr"] = "Executive Staff"  # Non-Bargaining, non-DoF
        sample_pula_staff_row["Status"] = "Active"  # No leave
        sample_pula_staff_row["Staff"] = "Regular"  # Not casual
        row = ReportRow(sample_pula_staff_row)
        result = row.position_number

        # Should return [N/A] as fallback and print warning to stderr
        assert result == "[N/A]"


class TestTermEndProperty:
    """Tests for term_end property."""

    def test_term_end_present(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test term_end returns date when present."""
        sample_pula_staff_row["Estimated Appt End Date"] = "12/31/2025 12:00:00 AM"
        row = ReportRow(sample_pula_staff_row)
        assert row.term_end == "12/31/2025 12:00:00 AM"

    def test_term_end_missing(self, sample_pula_staff_row: Dict[str, str]) -> None:
        """Test term_end returns empty string when missing."""
        sample_pula_staff_row.pop("Estimated Appt End Date", None)
        row = ReportRow(sample_pula_staff_row)
        assert row.term_end == ""

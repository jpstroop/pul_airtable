"""Tests for StaffReport class."""

# Standard library imports
from pathlib import Path

# Third party imports
import pytest

# Local imports
from staff_management.staff_report import StaffReport


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> str:
    """Create a temporary CSV file for testing.

    Uses anonymous test data with fictional names and employee IDs.
    """
    csv_content = """Emplid\tPreferred Else Primary First Name\tPreferred Else Primary Last Name\tE-Mail Address - Campus\tNet ID\tPosition Number\tUnion Code\tSal Plan Descr\tSal Plan\tDepartment Name\tDept\tPosition - Job Title\tGrade\tFTE\tHire Date\tRehire Date\tStatus\tStaff\tManager/Supervisor Emplid
123456789\tAlex\tSmith\tasmith@princeton.edu\tasmith\t00012345\tLIB\tLibrary Support Staff\tLS\tLib-Collections & Access Svcs\t31200\tLibrary Assistant\t7\t1.0\t1/15/2020 12:00:00 AM\t1/15/2020 12:00:00 AM\tActive\tRegular\t987654321
234567890\tJordan\tLee\tjlee@princeton.edu\tjlee\t\t\tRegular Professional Library\tLR\tLib-Data, Rsrch&Teaching Svcs\t31300\tLibrarian\t\t1.0\t7/1/2018 12:00:00 AM\t7/1/2018 12:00:00 AM\tActive\tRegular\t987654321
345678901\tTaylor\tChen\ttchen@princeton.edu\ttchen\t00034567\t\tReg Prof Specialist\tPS\tLibrary-Special Collections\t31400\tConservator\t\t1.0\t9/1/2019 12:00:00 AM\t9/1/2019 12:00:00 AM\tActive\tRegular\t987654321
987654321\tCameron\tMartinez\tcmartinez@princeton.edu\tcmartinez\t00098765\tLIB\tLibrary Support Staff\tLS\tLib-Administration\t31100\tDepartment Manager\t10\t1.0\t1/1/2015 12:00:00 AM\t1/1/2015 12:00:00 AM\tActive\tRegular\t"""

    csv_path = tmp_path / "test_report.csv"
    csv_path.write_text(csv_content, encoding="utf-16")
    return str(csv_path)


@pytest.fixture
def sample_csv_file_with_no_supervisor(tmp_path: Path) -> str:
    """Create a CSV file with an employee who has no supervisor."""
    csv_content = """Emplid\tPreferred Else Primary First Name\tPreferred Else Primary Last Name\tE-Mail Address - Campus\tNet ID\tPosition Number\tUnion Code\tSal Plan Descr\tSal Plan\tDepartment Name\tDept\tPosition - Job Title\tGrade\tFTE\tHire Date\tRehire Date\tStatus\tStaff\tManager/Supervisor Emplid
111111111\tCasey\tWong\tcwong@princeton.edu\tcwong\t00011111\tLIB\tLibrary Support Staff\tLS\tLib-Administration\t31100\tDirector\t12\t1.0\t1/1/2010 12:00:00 AM\t1/1/2010 12:00:00 AM\tActive\tRegular\t"""

    csv_path = tmp_path / "no_supervisor.csv"
    csv_path.write_text(csv_content, encoding="utf-16")
    return str(csv_path)


class TestStaffReportInit:
    """Tests for StaffReport initialization."""

    def test_loads_csv_successfully(self, sample_csv_file: str) -> None:
        """Test StaffReport loads CSV and creates ReportRow objects."""
        report = StaffReport(sample_csv_file)

        assert len(report.rows) == 4
        assert all(hasattr(row, "emplid") for row in report.rows)

    def test_parses_utf16_encoding(self, sample_csv_file: str) -> None:
        """Test that UTF-16 encoded CSV is parsed correctly."""
        report = StaffReport(sample_csv_file)

        # Verify data was parsed (not just empty rows)
        assert report.rows[0].first_name == "Alex"
        assert report.rows[1].first_name == "Jordan"


class TestGetRecordByEmplid:
    """Tests for get_record_by_emplid method."""

    def test_returns_record_when_found(self, sample_csv_file: str) -> None:
        """Test finding record by emplid."""
        report = StaffReport(sample_csv_file)

        record = report.get_record_by_emplid("123456789")

        assert record is not None
        assert record.emplid == "123456789"
        assert record.first_name == "Alex"
        assert record.last_name == "Smith"

    def test_returns_none_when_not_found(self, sample_csv_file: str) -> None:
        """Test get_record_by_emplid returns None when emplid not found."""
        report = StaffReport(sample_csv_file)

        record = report.get_record_by_emplid("999999999")

        assert record is None

    def test_finds_different_employees(self, sample_csv_file: str) -> None:
        """Test finding multiple different employees by emplid."""
        report = StaffReport(sample_csv_file)

        alex = report.get_record_by_emplid("123456789")
        jordan = report.get_record_by_emplid("234567890")

        assert alex is not None
        assert jordan is not None
        assert alex.first_name == "Alex"
        assert jordan.first_name == "Jordan"


class TestGetRecordByPositionNo:
    """Tests for get_record_by_position_no method."""

    def test_returns_record_when_found(self, sample_csv_file: str) -> None:
        """Test finding record by position number."""
        report = StaffReport(sample_csv_file)

        record = report.get_record_by_position_no("00012345")

        assert record is not None
        assert record.position_number == "00012345"
        assert record.first_name == "Alex"

    def test_returns_none_when_not_found(self, sample_csv_file: str) -> None:
        """Test get_record_by_position_no returns None when position not found."""
        report = StaffReport(sample_csv_file)

        record = report.get_record_by_position_no("99999999")

        assert record is None

    def test_finds_different_positions(self, sample_csv_file: str) -> None:
        """Test finding multiple different positions."""
        report = StaffReport(sample_csv_file)

        pos1 = report.get_record_by_position_no("00012345")
        pos2 = report.get_record_by_position_no("00034567")

        assert pos1 is not None
        assert pos2 is not None
        assert pos1.first_name == "Alex"
        assert pos2.first_name == "Taylor"


class TestAllEmpids:
    """Tests for all_emplids property."""

    def test_returns_all_employee_ids(self, sample_csv_file: str) -> None:
        """Test all_emplids returns all employee IDs with zero-padding."""
        report = StaffReport(sample_csv_file)

        emplids = report.all_emplids

        assert "123456789" in emplids
        assert "234567890" in emplids
        assert "345678901" in emplids
        assert "987654321" in emplids
        assert len(emplids) == 4

    def test_emplids_are_zero_padded(self, sample_csv_file: str) -> None:
        """Test that employee IDs are zero-padded to 9 digits."""
        report = StaffReport(sample_csv_file)

        emplids = report.all_emplids

        assert all(len(emplid) == 9 for emplid in emplids)


class TestAllPositionNumbers:
    """Tests for all_position_numbers property."""

    def test_returns_all_position_numbers(self, sample_csv_file: str) -> None:
        """Test all_position_numbers returns position numbers."""
        report = StaffReport(sample_csv_file)

        position_numbers = report.all_position_numbers

        assert "00012345" in position_numbers
        assert "00034567" in position_numbers
        assert "00098765" in position_numbers

    def test_excludes_dof_staff_without_positions(self, sample_csv_file: str) -> None:
        """Test that DoF staff without position numbers are excluded."""
        report = StaffReport(sample_csv_file)

        position_numbers = report.all_position_numbers

        # Jordan Lee (DoF Librarian) has no position number - should not be in list
        # Only 3 position numbers should be present
        assert len(position_numbers) == 3


class TestSupervisorHierarchy:
    """Tests for supervisor_hierarchy property."""

    def test_returns_employee_supervisor_tuples(self, sample_csv_file: str) -> None:
        """Test supervisor_hierarchy returns tuples of (employee, supervisor)."""
        report = StaffReport(sample_csv_file)

        hierarchy = report.supervisor_hierarchy

        assert len(hierarchy) == 4
        assert ("123456789", "987654321") in hierarchy
        assert ("234567890", "987654321") in hierarchy
        assert ("345678901", "987654321") in hierarchy

    def test_handles_no_supervisor(self, sample_csv_file_with_no_supervisor: str) -> None:
        """Test supervisor_hierarchy handles employees with no supervisor."""
        report = StaffReport(sample_csv_file_with_no_supervisor)

        hierarchy = report.supervisor_hierarchy

        assert len(hierarchy) == 1
        assert ("111111111", None) in hierarchy

    def test_top_level_manager_has_no_supervisor(self, sample_csv_file: str) -> None:
        """Test that top-level manager (Cameron) has no supervisor."""
        report = StaffReport(sample_csv_file)

        hierarchy = report.supervisor_hierarchy

        # Cameron Martinez (987654321) has empty supervisor field
        assert ("987654321", None) in hierarchy


class TestGroupedSupervisorHierarchy:
    """Tests for grouped_supervisor_hierarchy property."""

    def test_groups_employees_by_supervisor(self, sample_csv_file: str) -> None:
        """Test grouped_supervisor_hierarchy groups employees by their supervisor."""
        report = StaffReport(sample_csv_file)

        grouped = report.grouped_supervisor_hierarchy

        # Cameron Martinez (987654321) supervises 3 people
        assert "987654321" in grouped
        assert "123456789" in grouped["987654321"]
        assert "234567890" in grouped["987654321"]
        assert "345678901" in grouped["987654321"]
        assert len(grouped["987654321"]) == 3

    def test_includes_employees_without_supervisor(self, sample_csv_file_with_no_supervisor: str) -> None:
        """Test that employees without supervisors are included with None key."""
        report = StaffReport(sample_csv_file_with_no_supervisor)

        grouped = report.grouped_supervisor_hierarchy

        assert None in grouped
        assert "111111111" in grouped[None]

    def test_multiple_supervisors(self, sample_csv_file: str) -> None:
        """Test grouping with multiple supervisors."""
        report = StaffReport(sample_csv_file)

        grouped = report.grouped_supervisor_hierarchy

        # Should have 2 groups: one for supervisor 987654321, one for None
        assert len(grouped) == 2
        assert "987654321" in grouped
        assert None in grouped

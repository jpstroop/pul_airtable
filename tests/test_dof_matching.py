"""Tests for Dean of the Faculty staff name-based matching logic.

These tests verify the DoF staff identification and matching behavior.
"""

# Standard library imports
from typing import Dict

# Third party imports
import pytest

# Local imports
from staff_management.report_row import ReportRow


def test_dof_librarian_identified(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test that DoF Librarians are correctly identified."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.is_dof_staff is True
    assert row.admin_group == "DoF: Librarian"


def test_dof_specialist_identified(sample_dof_specialist_row: Dict[str, str]) -> None:
    """Test that DoF Professional Specialists are correctly identified."""
    row = ReportRow(sample_dof_specialist_row)
    assert row.is_dof_staff is True
    assert row.admin_group == "DoF: Professional Specialist"


def test_pula_staff_not_dof(sample_pula_staff_row: Dict[str, str]) -> None:
    """Test that PULA staff are not identified as DoF."""
    row = ReportRow(sample_pula_staff_row)
    assert row.is_dof_staff is False
    assert row.admin_group == "HR: PULA"


def test_dof_staff_use_name_for_matching(sample_dof_librarian_row: Dict[str, str]) -> None:
    """Test that DoF staff have predictable names for matching."""
    row = ReportRow(sample_dof_librarian_row)
    assert row.is_dof_staff is True
    assert row.preferred_name == "Jordan Lee"
    # In sync logic, this name would be used for matching via get_record_by_name()


# Integration tests (require test Airtable base)
# Mark as integration tests that need special setup


@pytest.mark.integration
@pytest.mark.skip(reason="Requires test Airtable base setup")
def test_get_record_by_name_finds_matching_dof_staff() -> None:
    """Test StaffAirtable.get_record_by_name() finds DoF staff by name.

    This test requires:
    - Test Airtable base with known DoF staff records
    - Credentials configured for test environment
    """
    # TODO: Implement when test Airtable base is configured
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="Requires test Airtable base setup")
def test_sync_matches_dof_staff_by_name_when_emplid_missing() -> None:
    """Test that sync logic uses name matching for DoF staff.

    Scenario:
    - DoF staff person in CSV (new emplid)
    - Matching name exists in Airtable (vacancy or existing record)
    - Should match by name and update that record

    This test requires:
    - Test Airtable base with vacancy records
    - Test CSV data
    """
    # TODO: Implement when test Airtable base is configured
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="Requires test Airtable base setup")
def test_sync_prompts_for_new_dof_staff_without_name_match() -> None:
    """Test that sync logic exits with prompt for new DoF staff.

    Scenario:
    - DoF staff person in CSV
    - No emplid match, no name match in Airtable
    - Should exit with message about CLI prompt needed

    This test requires:
    - Test Airtable base
    - Test CSV data with new DoF staff
    """
    # TODO: Implement when test Airtable base is configured
    # TODO: In Phase 5 (CLI), this should become an interactive prompt test
    pass

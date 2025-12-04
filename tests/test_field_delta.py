# Standard library imports
from typing import Any
from typing import Dict
from typing import Tuple
from unittest.mock import patch

# Third party imports
from pyairtable.api.types import Fields
from pytest import CaptureFixture

# Local imports
from staff_management.field_delta import FieldDelta


class TestComputeDelta:
    """Tests for FieldDelta.compute_delta()"""

    def test_no_changes_returns_empty_dict(self) -> None:
        """Should return empty dict when no fields changed."""
        old_fields: Fields = {"Title": "Associate", "Department": "Library Services"}
        new_fields: Fields = {"Title": "Associate", "Department": "Library Services"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_single_field_change(self) -> None:
        """Should return dict with one entry for single field change."""
        old_fields: Fields = {"Title": "Associate", "Department": "Library Services"}
        new_fields: Fields = {"Title": "Senior", "Department": "Library Services"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert len(result) == 1
        assert "Title" in result
        assert result["Title"] == ("Associate", "Senior")

    def test_multiple_field_changes(self) -> None:
        """Should return dict with all changed fields."""
        old_fields: Fields = {"Title": "Associate", "Grade": "P3", "Department": "IT"}
        new_fields: Fields = {"Title": "Senior", "Grade": "P4", "Department": "IT"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert len(result) == 2
        assert result["Title"] == ("Associate", "Senior")
        assert result["Grade"] == ("P3", "P4")

    def test_handles_none_to_value(self) -> None:
        """Should detect change from None to value."""
        old_fields: Fields = {"pul:FWA/Hours": None}
        new_fields: Fields = {"pul:FWA/Hours": "Remote - 40hrs"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["pul:FWA/Hours"] == (None, "Remote - 40hrs")

    def test_handles_value_to_none(self) -> None:
        """Should detect change from value to None."""
        old_fields: Fields = {"pul:FWA/Hours": "Remote - 40hrs"}
        new_fields: Fields = {"pul:FWA/Hours": None}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["pul:FWA/Hours"] == ("Remote - 40hrs", None)

    def test_ignores_unchanged_fields(self) -> None:
        """Should not include fields that didn't change."""
        old_fields: Fields = {"Title": "Associate", "Grade": "P3", "Department": "IT", "pul:On Leave?": False}
        new_fields: Fields = {"Title": "Senior", "Grade": "P3", "Department": "IT", "pul:On Leave?": False}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert len(result) == 1
        assert "Title" in result
        assert "Grade" not in result
        assert "Department" not in result
        assert "pul:On Leave?" not in result

    def test_handles_boolean_changes(self) -> None:
        """Should detect boolean field changes."""
        old_fields: Fields = {"pul:On Leave?": False}
        new_fields: Fields = {"pul:On Leave?": True}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["pul:On Leave?"] == (False, True)

    def test_handles_list_changes(self) -> None:
        """Should detect list field changes."""
        old_fields: Fields = {"Manager/Supervisor": ["recABC"]}
        new_fields: Fields = {"Manager/Supervisor": ["recXYZ"]}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["Manager/Supervisor"] == (["recABC"], ["recXYZ"])

    def test_handles_missing_field_in_old(self) -> None:
        """Should detect when field exists in new but not old."""
        old_fields: Fields = {"Title": "Associate"}
        new_fields: Fields = {"Title": "Associate", "NewField": "value"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["NewField"] == (None, "value")

    def test_treats_none_and_empty_list_as_equal(self) -> None:
        """Should not report change when None becomes empty list (semantically equal)."""
        old_fields: Fields = {"End Date": None}
        new_fields: Fields = {"End Date": []}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_empty_list_and_none_as_equal(self) -> None:
        """Should not report change when empty list becomes None (semantically equal)."""
        old_fields: Fields = {"End Date": []}
        new_fields: Fields = {"End Date": None}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_none_and_false_as_equal(self) -> None:
        """Should not report change when None becomes False (semantically equal)."""
        old_fields: Fields = {"pul:On Leave?": None}
        new_fields: Fields = {"pul:On Leave?": False}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_false_and_none_as_equal(self) -> None:
        """Should not report change when False becomes None (semantically equal)."""
        old_fields: Fields = {"pul:On Leave?": False}
        new_fields: Fields = {"pul:On Leave?": None}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_detects_true_vs_none_as_change(self) -> None:
        """Should detect change when None becomes True (different values)."""
        old_fields: Fields = {"pul:On Leave?": None}
        new_fields: Fields = {"pul:On Leave?": True}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["pul:On Leave?"] == (None, True)

    def test_detects_nonempty_list_vs_none_as_change(self) -> None:
        """Should detect change when None becomes non-empty list (different values)."""
        old_fields: Fields = {"Manager/Supervisor": None}
        new_fields: Fields = {"Manager/Supervisor": ["recABC"]}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["Manager/Supervisor"] == (None, ["recABC"])

    def test_treats_none_and_list_with_empty_string_as_equal(self) -> None:
        """Should not report change when None becomes list with empty string (semantically equal)."""
        old_fields: Fields = {"End Date": None}
        new_fields: Fields = {"End Date": [""]}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_none_and_list_with_none_as_equal(self) -> None:
        """Should not report change when None becomes list containing None (semantically equal)."""
        old_fields: Fields = {"End Date": None}
        new_fields: Fields = {"End Date": [None]}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_date_with_and_without_time_as_equal(self) -> None:
        """Should not report change when date string gains midnight time component."""
        old_fields: Fields = {"End Date": "2027-07-01"}
        new_fields: Fields = {"End Date": "2027-07-01 00:00:00"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_date_in_list_with_and_without_time_as_equal(self) -> None:
        """Should not report change when date string in list gains midnight time component."""
        old_fields: Fields = {"End Date": ["2027-07-01"]}
        new_fields: Fields = {"End Date": ["2027-07-01 00:00:00"]}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_detects_date_with_nonmidnight_time_as_change(self) -> None:
        """Should detect change when date string gains non-midnight time component."""
        old_fields: Fields = {"End Date": "2027-07-01"}
        new_fields: Fields = {"End Date": "2027-07-01 14:30:00"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result["End Date"] == ("2027-07-01", "2027-07-01 14:30:00")

    def test_treats_none_and_empty_string_as_equal(self) -> None:
        """Should not report change when None becomes empty string (semantically equal)."""
        old_fields: Fields = {"End Date": None}
        new_fields: Fields = {"End Date": ""}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_none_and_whitespace_string_as_equal(self) -> None:
        """Should not report change when None becomes whitespace-only string (semantically equal)."""
        old_fields: Fields = {"End Date": None}
        new_fields: Fields = {"End Date": "   "}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}

    def test_treats_strings_with_different_whitespace_as_equal(self) -> None:
        """Should not report change when only whitespace (newlines, tabs, spaces) differs."""
        old_fields: Fields = {"Title": "Executive Head and Associate University Librarian"}
        new_fields: Fields = {"Title": "Executive Head and\nAssociate University Librarian"}

        result = FieldDelta.compute_delta(old_fields, new_fields)

        assert result == {}


class TestFormatValue:
    """Tests for FieldDelta.format_value()"""

    def test_formats_none_as_empty(self) -> None:
        """Should format None as '(empty)'."""
        result = FieldDelta.format_value(None)
        assert result == "(empty)"

    def test_formats_boolean_true(self) -> None:
        """Should format True as 'True'."""
        result = FieldDelta.format_value(True)
        assert result == "True"

    def test_formats_boolean_false(self) -> None:
        """Should format False as 'False'."""
        result = FieldDelta.format_value(False)
        assert result == "False"

    def test_formats_string(self) -> None:
        """Should format string with quotes."""
        result = FieldDelta.format_value("Test String")
        assert result == '"Test String"'

    def test_formats_number(self) -> None:
        """Should format number as string."""
        result = FieldDelta.format_value(42)
        assert result == "42"

    def test_formats_empty_list(self) -> None:
        """Should format empty list as '(empty)'."""
        result = FieldDelta.format_value([])
        assert result == "(empty)"

    def test_formats_list_with_items(self) -> None:
        """Should format list with brackets and quoted strings."""
        result = FieldDelta.format_value(["recABC", "recXYZ"])
        assert result == '["recABC", "recXYZ"]'

    def test_formats_list_with_mixed_types(self) -> None:
        """Should format list with mixed types, quoting strings."""
        result = FieldDelta.format_value(["text", 123, True])
        assert result == '["text", 123, True]'


class TestDisplayChanges:
    """Tests for FieldDelta.display_changes()"""

    def test_displays_single_change(self, capsys: CaptureFixture[str]) -> None:
        """Should display one line for single field change."""
        delta: Dict[str, Tuple[Any, Any]] = {"Title": ("Associate", "Senior")}

        with patch("staff_management.field_delta.echo") as mock_echo:
            FieldDelta.display_changes("Jane Doe", delta)

            mock_echo.assert_called_once()
            call_args = mock_echo.call_args[0][0]
            assert "Jane Doe" in str(call_args)
            assert "Title" in str(call_args)
            assert "changed from" in str(call_args)
            assert '"Associate"' in str(call_args)
            assert '"Senior"' in str(call_args)

    def test_displays_multiple_changes(self) -> None:
        """Should display multiple lines for multiple changes."""
        delta: Dict[str, Tuple[Any, Any]] = {
            "Title": ("Associate", "Senior"),
            "Grade": ("P3", "P4"),
            "pul:On Leave?": (False, True),
        }

        with patch("staff_management.field_delta.echo") as mock_echo:
            FieldDelta.display_changes("John Smith", delta)

            assert mock_echo.call_count == 3
            # Check that each field was displayed
            all_calls = [str(call[0][0]) for call in mock_echo.call_args_list]
            assert any("Title" in call for call in all_calls)
            assert any("Grade" in call for call in all_calls)
            assert any("pul:On Leave?" in call for call in all_calls)

    def test_displays_nothing_for_empty_delta(self) -> None:
        """Should not display anything when delta is empty."""
        delta: Dict[str, Tuple[Any, Any]] = {}

        with patch("staff_management.field_delta.echo") as mock_echo:
            FieldDelta.display_changes("Jane Doe", delta)

            mock_echo.assert_not_called()

    def test_formats_values_in_display(self) -> None:
        """Should use format_value for both old and new values."""
        delta: Dict[str, Tuple[Any, Any]] = {"pul:On Leave?": (False, True), "pul:FWA/Hours": (None, "Remote")}

        with patch("staff_management.field_delta.echo") as mock_echo:
            FieldDelta.display_changes("Taylor Lee", delta)

            all_calls = [str(call[0][0]) for call in mock_echo.call_args_list]
            # Check boolean formatting (False and True, not quoted)
            assert any("False" in call and "True" in call for call in all_calls)
            # Check None formatting ((empty) and quoted string for non-boolean fields)
            assert any("(empty)" in call and '"Remote"' in call for call in all_calls)

    def test_displays_none_as_false_for_boolean_fields(self) -> None:
        """Should display None as False for boolean fields."""
        delta: Dict[str, Tuple[Any, Any]] = {"pul:On Leave?": (None, True)}

        with patch("staff_management.field_delta.echo") as mock_echo:
            FieldDelta.display_changes("Jane Doe", delta)

            call_args = str(mock_echo.call_args[0][0])
            # None should be displayed as False for boolean field
            assert "False" in call_args
            assert "True" in call_args
            assert "(empty)" not in call_args

# Standard library imports
from typing import Any
from typing import Dict
from typing import Tuple

# Third party imports
from click import echo
from click import style as click_style
from pyairtable.api.types import Fields


class FieldDelta:
    """Computes and displays field changes between old and new records.

    All methods are static as this class has no state.
    Used for verbose mode to show what fields changed during sync.
    """

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Normalize values for comparison to avoid false positives.

        Treats semantically equivalent values as equal:
        - None, [], and lists with only empty values are "empty"
        - None and False are both "false/off"
        - Date strings with/without time component (00:00:00) are equal

        Args:
            value: Value to normalize

        Returns:
            Normalized value for comparison
        """
        if value is None:
            return None
        if value is False:
            return None
        # Treat empty/whitespace-only strings as None
        if isinstance(value, str) and value.strip() == "":
            return None
        # Normalize whitespace in strings (collapse newlines, tabs, multiple spaces to single space)
        if isinstance(value, str):
            # Standard library imports
            import re

            normalized = re.sub(r"\s+", " ", value.strip())
            return FieldDelta._normalize_date_string(normalized)
        if isinstance(value, list):
            # Filter out empty/None values from list
            # Also filter whitespace-only strings
            def is_empty(v: Any) -> bool:
                if v in (None, "", []):
                    return True
                if isinstance(v, str) and v.strip() == "":
                    return True
                return False

            non_empty = [v for v in value if not is_empty(v)]
            if len(non_empty) == 0:
                return None
            # Normalize date strings in list
            normalized_list = [FieldDelta._normalize_date_string(v) for v in non_empty]
            return normalized_list
        # Normalize date strings
        if isinstance(value, str):
            return FieldDelta._normalize_date_string(value)
        return value

    @staticmethod
    def _normalize_date_string(value: Any) -> Any:
        """Normalize date strings to remove midnight time component.

        Treats '2027-07-01' and '2027-07-01 00:00:00' as equal.

        Args:
            value: Value to normalize

        Returns:
            Normalized value
        """
        if isinstance(value, str) and " 00:00:00" in value:
            return value.replace(" 00:00:00", "")
        return value

    @staticmethod
    def compute_delta(old_fields: Fields, new_fields: Fields) -> Dict[str, Tuple[Any, Any]]:
        """Return dict of {field_name: (old_value, new_value)} for changed fields.

        Only includes fields that actually changed between old and new.
        Normalizes values to avoid reporting semantically equivalent changes:
        - None vs [] (empty list) are treated as equal
        - None vs False are treated as equal

        Args:
            old_fields: Current fields from Airtable
            new_fields: New fields from CSV

        Returns:
            Dict with entries only for fields that changed
        """
        delta: Dict[str, Tuple[Any, Any]] = {}

        # Check all fields in new_fields
        for field_name, new_value in new_fields.items():
            old_value = old_fields.get(field_name)
            # Normalize for comparison to avoid false positives
            if FieldDelta._normalize_value(old_value) != FieldDelta._normalize_value(new_value):
                delta[field_name] = (old_value, new_value)

        return delta

    @staticmethod
    def format_value(value: Any) -> str:
        """Format a field value for display.

        Formatting rules:
        - None: (empty)
        - bool: True/False (no quotes)
        - strings: "value" (quoted)
        - numbers: 42 (no quotes)
        - lists: [item1, item2] (bracketed)

        Args:
            value: Field value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "(empty)"
        if isinstance(value, bool):
            return str(value)  # True or False
        if isinstance(value, list):
            if not value:
                return "(empty)"
            # Format list items
            formatted_items = [FieldDelta._format_list_item(v) for v in value]
            return "[" + ", ".join(formatted_items) + "]"
        if isinstance(value, str):
            return f'"{value}"'
        # Numbers and other types
        return str(value)

    @staticmethod
    def _format_list_item(value: Any) -> str:
        """Format a single item within a list."""
        if value is None:
            return "(empty)"
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    @staticmethod
    def display_changes(name: str, delta: Dict[str, Tuple[Any, Any]]) -> None:
        """Display changes line-by-line.

        Format: "Name field changed from old to new"
        - Strings are quoted: "value"
        - Booleans: True/False (None treated as False for boolean fields)
        - Numbers/dates: unquoted
        - Lists: [item1, item2]

        Args:
            name: Person's name
            delta: Dict of field changes {field_name: (old_value, new_value)}
        """
        for field_name, (old_val, new_val) in delta.items():
            # For boolean fields, treat None as False for display
            is_bool_field = isinstance(old_val, bool) or isinstance(new_val, bool)
            if is_bool_field:
                old_val = False if old_val is None else old_val
                new_val = False if new_val is None else new_val

            old_str = FieldDelta.format_value(old_val)
            new_str = FieldDelta.format_value(new_val)
            echo(  # pragma: no cover
                click_style(f"  → {name} {field_name} changed from {old_str} to {new_str}", fg="cyan")
            )

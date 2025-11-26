# Standard library imports
from sys import stderr
from typing import cast

# Third party imports
from pyairtable.api.types import Fields

# Local imports
from staff_management.report_row import ReportRow
from staff_management.staff_airtable import AirtableRecord
from staff_management.staff_airtable import JSONDict


class FieldMapper:
    """Transforms data between CSV report rows and Airtable field format.

    Pure transformation logic with no side effects - fully testable without mocking.
    """

    @staticmethod
    def extract_fields(record: AirtableRecord) -> JSONDict:
        """Extract fields dict from Airtable record with type narrowing.

        Args:
            record: Airtable record containing fields dict

        Returns:
            Fields dictionary cast to JSONDict type
        """
        return cast(JSONDict, record["fields"])

    @staticmethod
    def map_row_to_fields(report_row: ReportRow) -> Fields:
        """Transform CSV report row to Airtable field format.

        Maps all ReportRow properties to their corresponding Airtable field names.

        Args:
            report_row: CSV row wrapper with property-based access

        Returns:
            Fields dictionary ready for Airtable create/update operations

        Raises:
            Exception: Re-raises any exception after logging the emplid for debugging
        """
        try:
            data: Fields = {}
            data["University ID"] = report_row.emplid
            data["Division"] = report_row.division
            data["Admin. Group"] = report_row.admin_group
            data["pul:Search Status"] = "Hired"
            data["University Phone"] = report_row.phone
            data["End Date"] = report_row.term_end
            data["Term/Perm/CA Track"] = report_row.term_perm
            data["Title"] = report_row.title
            data["pul:Preferred Name"] = report_row.preferred_name
            data["Email"] = report_row.email
            data["Last Name"] = report_row.last_name
            data["First Name"] = report_row.first_name
            data["Time"] = report_row.time
            data["Start Date"] = report_row.start_date
            data["Rehire Date"] = report_row.rehire_date
            data["Grade"] = report_row.grade
            data["Sal. Plan"] = report_row.get("Sal Plan")
            data["Position Number"] = report_row.position_number
            data["Address"] = report_row.address
            netid = report_row["Net ID"]
            data["netid"] = netid
            data["PS Department Name"] = report_row.ps_department_name
            data["PS Department Code"] = report_row.ps_department_code
            # HR staff: Check Status field for "Leave With Pay"
            # DoF staff: If in CSV, they're active (DoF on leave disappear from CSV)
            data["pul:On Leave?"] = report_row.status == "Leave With Pay"

        except Exception as e:
            print(f"Error with emplid {report_row.emplid}", file=stderr)
            raise e

        return data

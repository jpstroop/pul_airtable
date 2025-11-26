# Standard library imports
from datetime import date
from re import sub
from sys import stderr
from time import sleep
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union
from typing import cast

# Third party imports
from click import echo
from click import style as click_style
from pyairtable import Api
from pyairtable import Table
from pyairtable.api.types import Fields
from pyairtable.api.types import RecordDict
from pyairtable.api.types import UpdateRecordDict

if TYPE_CHECKING:
    # Local imports
    from staff_management.staff_report import StaffReport

# JSON type hierarchy per CLAUDE.md standards
type JSONPrimitive = Union[str, int, float, bool, None]
type JSONType = Union[Dict[str, "JSONType"], List["JSONType"], JSONPrimitive]
type JSONDict = Dict[str, JSONType]
type JSONList = List[JSONType]

# Airtable record type - use pyairtable's RecordDict
type AirtableRecord = RecordDict


class StaffAirtable:

    VACANT_IMAGE: str = "https://raw.githubusercontent.com/jpstroop/pul_airtable/main/vacant.png"
    NO_PHOTO_IMAGE: str = "https://raw.githubusercontent.com/jpstroop/pul_airtable/main/no_photo.png"

    _main_table: Table
    _removal_history_table: Table
    _next_vacancy_number: Optional[int]

    def __init__(
        self, personal_access_token: str, base_id: str, all_staff_table_id: str, history_table_id: str
    ) -> None:
        api = Api(personal_access_token)
        self._main_table = api.table(base_id, all_staff_table_id)
        self._removal_history_table = api.table(base_id, history_table_id)
        self._next_vacancy_number = None

    @property
    def next_vacancy(self) -> str:
        if not self._next_vacancy_number:
            formula = "REGEX_MATCH({pul:Preferred Name}, '^__VACANCY')"
            records = self._main_table.all(formula=formula, sort=["pul:Preferred Name"])
            last = sub(r"[^\d]", "", str(records[-1]["fields"]["pul:Preferred Name"]))
            self._next_vacancy_number = int(last) + 1
        else:
            self._next_vacancy_number += 1
        return f"__VACANCY_{str(self._next_vacancy_number).zfill(3)}__"

    @property
    def all_emplids(self) -> List[str]:
        ids = self._main_table.all(fields=("University ID"))
        return [str(i["fields"]["University ID"]).zfill(9) for i in ids if i["fields"].get("University ID")]

    @property
    def all_position_numbers(self) -> List[str]:
        nos = self._main_table.all(fields=("Position Number"))
        filt = lambda pn: not pn.startswith("[") and pn != ""
        return list(filter(filt, [str(n["fields"].get("Position Number", "")) for n in nos]))

    @property
    def all_vacancies(self) -> List[AirtableRecord]:
        formula = "REGEX_MATCH({pul:Preferred Name}, '^__VACANCY')"
        return self._main_table.all(formula=formula, sort=["pul:Preferred Name"])

    @property
    def all_vacancy_position_ids(self) -> List[str]:
        """This is the position number for HR jobs, and the name of the last
        occupant for DoF jobs.
        """
        return []

    @property
    def all_staff(self) -> List[AirtableRecord]:
        data = self._main_table.all()
        l = lambda r: not str(r["fields"].get("pul:Preferred Name", "")).startswith("__")
        return list(filter(l, data))

    @property
    def all_pula_managers(self) -> List[AirtableRecord]:
        fields = ("pul:Preferred Name", "University ID", "Manager/Supervisor", "Admin. Group", "Is Supervisor?")
        data = self._main_table.all(fields=fields)
        managers = list(filter(lambda r: "Is Supervisor?" in r["fields"], data))
        return [m for m in managers if self.has_pula_staff(m, data=data)]

    @property
    def all_dof_librarian_managers(self) -> List[AirtableRecord]:
        fields = ("pul:Preferred Name", "University ID", "Manager/Supervisor", "Admin. Group", "Is Supervisor?")
        data = self._main_table.all(fields=fields)
        managers = list(filter(lambda r: "Is Supervisor?" in r["fields"], data))
        return [m for m in managers if self.has_dof_librarian_staff(m, data=data)]

    def get_managers_employees(
        self, manager_obj: AirtableRecord, data: Optional[List[AirtableRecord]] = None
    ) -> List[AirtableRecord]:
        # TODO: do we need to break out a Manager object? And an Employee/Person object (superclass)?
        # this could encapsulate the mapping between CSV reports and AT (constructors for both)
        # and this could be an iterator (.employees)
        """Get employees of a manager.
        manager needs an object because because some mgrs are vacant (no emplid)
        data is a list of all staff; a cached copy of the table.
        """
        if data is None:
            data = self._main_table.all()
        mgr_id = manager_obj["id"]  # working with AT ids because some mgrs are vacant
        filt = lambda r: mgr_id in r["fields"].get("Manager/Supervisor", [])
        employees = list(filter(filt, data))
        return employees

    def has_pula_staff(self, mgr_obj: AirtableRecord, data: Optional[List[AirtableRecord]] = None) -> bool:
        if data is None:
            data = self._main_table.all()
        employees = self.get_managers_employees(mgr_obj, data)
        any_pula = any([e["fields"].get("Admin. Group") == "HR: PULA" for e in employees])
        supervisors = filter(lambda e: "Is Supervisor?" in e["fields"], employees)
        if any_pula:
            return True
        elif supervisors:
            # note the recursion here
            any_pula = any([self.has_pula_staff(s, data) for s in supervisors])
            return any_pula
        else:
            return False

    def has_dof_librarian_staff(self, mgr_obj: AirtableRecord, data: Optional[List[AirtableRecord]] = None) -> bool:
        if data is None:
            data = self._main_table.all()
        employees = self.get_managers_employees(mgr_obj, data)
        any_dof = any([e["fields"].get("Admin. Group") == "DoF: Librarian" for e in employees])
        supervisors = filter(lambda e: "Is Supervisor?" in e["fields"], employees)
        if any_dof:
            return True
        elif supervisors:
            # note the recursion here
            any_dof = any([self.has_dof_librarian_staff(s, data) for s in supervisors])
            return any_dof
        else:
            return False

    def get_record_by_emplid(self, emplid: str) -> Optional[AirtableRecord]:
        return self._main_table.first(formula=f'{{University ID}} = "{emplid}"')

    def get_record_by_position_no(self, pn: str) -> Optional[AirtableRecord]:
        return self._main_table.first(formula=f'{{Position Number}} = "{pn}"')

    def get_record_by_name(self, name: str) -> Optional[AirtableRecord]:
        """Find record by preferred name. Used primarily for DoF staff without position numbers."""
        return self._main_table.first(formula=f'{{pul:Preferred Name}} = "{name}"')

    def get_record_by_at_id(self, at_id: str) -> AirtableRecord:
        return self._main_table.get(at_id)

    def add_new_record(self, data: Fields, by_pn: bool = False) -> None:
        emplid = data["University ID"]
        if self.get_record_by_emplid(str(emplid)):
            name = data["pul:Preferred Name"]
            print(f"ERROR: A record already exists for {emplid} ({name})", file=stderr)
            raise Exception(f"A record already exists for {emplid} ({name})")
        else:
            self._main_table.create(data, typecast=True)
            echo(click_style(f'Added {emplid} ({data["pul:Preferred Name"]})', fg="green"))

    def update_record(self, record_id: str, data: Fields, log: bool = False) -> None:
        if log:
            # Note: this will fail when an existing person moves to DoF
            position_no = data.get("Position Number")
            emplid = data["University ID"]
            echo(
                click_style(f'Updated position {position_no} with {emplid} ({data["pul:Preferred Name"]})', fg="green")
            )
        self._main_table.update(record_id, data, typecast=True)

    def delete_record(self, record_id: str) -> None:
        """Delete a record from the main table.

        Use this for casual employees or eliminated positions that don't need a vacancy.
        """
        self._main_table.delete(record_id)

    def employee_to_vacancy(self, emplid: str) -> None:
        airtable_record = self.get_record_by_emplid(emplid)
        if airtable_record is None:
            raise Exception(f"No record found for emplid {emplid}")
        airtable_fields = airtable_record["fields"]
        vacancy_data = cast(
            Fields,
            {
                "Email": None,
                "First Name": None,
                "Headshot": [{"url": StaffAirtable.VACANT_IMAGE}],
                "Last Name": None,
                "Last Occupant": airtable_fields["pul:Preferred Name"],
                "netid": None,
                "pul:Preferred Name": self.next_vacancy,
                "pul:Search Status": "Recently Vacated",
                "End Date": None,
                "Start Date": None,
                "Rehire Date": None,
                "University ID": None,
                "University Phone": None,
                "pul:FWA/Hours": None,
                "pul:Anticipated End Date": None,
            },
        )
        supervisor_id_list = airtable_fields["Manager/Supervisor"]
        if isinstance(supervisor_id_list, list) and len(supervisor_id_list) > 0:
            supervisor_fields = self.get_record_by_at_id(str(supervisor_id_list[0]))["fields"]
        else:
            supervisor_fields = {}
        removal_data = cast(
            Fields,
            {
                "Name": airtable_fields["pul:Preferred Name"],
                "netid": airtable_fields["netid"],
                "Title": airtable_fields["Title"],
                "Position Number": airtable_fields["Position Number"],
                "Division": airtable_fields["Division"],
                "Supervisor": supervisor_fields.get("pul:Preferred Name", ""),
                "Removed from AT": date.today().isoformat(),
            },
        )
        self._main_table.update(str(airtable_record["id"]), vacancy_data)
        self._removal_history_table.create(removal_data, typecast=True)
        echo(
            click_style(
                f'Created {vacancy_data["pul:Preferred Name"]} (was {airtable_fields["pul:Preferred Name"]})',
                fg="green",
            )
        )

    def update_pula_supervisor_statuses(self) -> None:
        updates: List[UpdateRecordDict] = []
        for pm in self.all_pula_managers:
            update = cast(UpdateRecordDict, {"id": pm["id"], "fields": {"Is PULA Supervisor?": True}})
            updates.append(update)
        self._main_table.batch_update(updates)

    def update_dof_librarian_supervisor_statuses(self) -> None:
        updates: List[UpdateRecordDict] = []
        for pm in self.all_dof_librarian_managers:
            update = cast(UpdateRecordDict, {"id": pm["id"], "fields": {"Is DoF Librarian Supervisor?": True}})
            updates.append(update)
        self._main_table.batch_update(updates)

    def clear_supervisor_statuses(self) -> None:
        updates: List[UpdateRecordDict] = []
        for emp in self.all_staff:
            d = cast(
                UpdateRecordDict, {"id": emp["id"], "fields": {"Is Supervisor?": False, "Is PULA Supervisor?": False}}
            )
            updates.append(d)
        self._main_table.batch_update(updates)

    def update_supervisor_hierarchy(self, staff_report: "StaffReport", throttle_interval: float) -> None:

        for empl, supr in staff_report.supervisor_hierarchy:
            try:
                employee_record = self.get_record_by_emplid(empl)  # TODO: Will error if not found
                supervisor_record = self.get_record_by_emplid(str(supr)) if supr else None
                if employee_record is None or supervisor_record is None:
                    continue
                updates: List[UpdateRecordDict] = [
                    cast(UpdateRecordDict, {"id": supervisor_record["id"], "fields": {"Is Supervisor?": True}}),
                    cast(
                        UpdateRecordDict,
                        {"id": employee_record["id"], "fields": {"Manager/Supervisor": [supervisor_record["id"]]}},
                    ),
                ]
                self._main_table.batch_update(updates)
            except Exception as e:  # Change to just handle KeyErrors?
                empl_name = (
                    employee_record.get("fields", {}).get("pul:Preferred Name") if employee_record else "Unknown"
                )
                if supervisor_record is None:
                    print(f"{empl_name} lacks a supervisor", file=stderr)
                else:
                    print(f"Error with {empl_name}: {str(e)}", file=stderr)
                    # Debug info available but not printed to avoid type issues
                    # Employee: employee_record, Supervisor: supervisor_record
            sleep(throttle_interval)

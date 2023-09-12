# Start with a dowload of "Data for Org Chart" (the filters and having AJ first are important)
from csv import DictReader
from main import print_json
from sys import stdout

with open('./All Staff-Data for Org Chart.csv', 'r', encoding='utf-8-sig') as f:
    ROWS = [r for r in DictReader(f)]

INDENT = '        '

def format_entry(row, leading_space):
    entry = f"{leading_space}Name: {row['pul:Preferred Name']}"
    entry += f"\n{leading_space}Title: {row['Title']}"
    if row.get("pul:Team"):
        entry += f"\n{leading_space}Team: {row['pul:Team']}"
    elif row.get("pul:Unit"):
        entry += f"\n{leading_space}Unit: {row['pul:Unit']}"
    elif row.get("pul:Department"):
        entry += f"\n{leading_space}Department: {row['pul:Department']}"
    else:
        entry += f"\n{leading_space}Division: {row['Division']}"
    if row.get('pul:Ad hoc Groups'):
        entry += f"\n{leading_space}Groups: {', '.join(row['pul:Ad hoc Groups'].split(','))}"
    entry += f"\n{leading_space}Link: https://library.princeton.edu/staff/{row['netid']}"
    entry += "\n"
    return entry

def list_reports(row, leading_space, f=stdout):
    print(format_entry(row, leading_space=leading_space), file=stdout)
    reports = get_reports(row)
    # recursive case
    if reports:
        leading_space = leading_space + INDENT
        for report in reports:
            list_reports(report, leading_space)
    # base case is to do nothing

def reports_sort_key(row):
    return (
        row['Is Supervisor?'],
        row["Last Name"],
        row['pul:Preferred Name'].startswith('__VACANCY')
    )

def get_reports(supervisor_row):
    l = [r for r in ROWS if r["Manager/Supervisor"] == supervisor_row["pul:Preferred Name"]]
    l.sort(key=reports_sort_key)
    return l

if __name__ == "__main__":
    list_reports(ROWS[0], INDENT)

# print_json(row)
# {
#   "pul:Preferred Name": "Sarah E Reiff Conell",
#   "Title": "Research Data Management Specialist",
#   "Is Supervisor?": "",
#   "Manager/Supervisor": "Wind Cowles",
#   "netid": "sr7276",
#   "Org Chart Sort": "5.0",
#   "Division": "Lib-Data, Rsrch&Teaching Svcs",
#   "pul:Department": "Research Data and Open Scholarship",
#   "pul:Unit": "Princeton Research Data Service",
#   "pul:Team": "",
#   "Admin. Group": "HR: Non-Bargaining",
#   "pul:Building": "Firestone Library",
#   "pul:Ad hoc Groups": ""
# }



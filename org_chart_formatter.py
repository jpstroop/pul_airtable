# Start with a dowload of "Data for Org Chart" (the filters and having AJ first are important)
from csv import DictReader
from main import print_json
from sys import stdout

with open('./All Staff-Data for Org Chart.csv', 'r', encoding='utf-8-sig') as f:
    ROWS = [r for r in DictReader(f)]

# TODO: get data directly from AirTable

INDENT = '\t'



def format_entry(row, leading_space=''):
    entry = f"{leading_space}{row['pul:Preferred Name']}"
    entry += f"\n{leading_space}{row['Title']}"
    if row.get("pul:Team"):
        entry += f"\n{leading_space}{row['pul:Team']}"
    elif row.get("pul:Unit"):
        entry += f"\n{leading_space}{row['pul:Unit']}"
    elif row.get("pul:Department"):
        entry += f"\n{leading_space}{row['pul:Department']}"
    else:
        entry += f"\n{leading_space}{row['Division']}"
    if row.get('pul:Ad hoc Groups'):
        entry += f"\n{leading_space}Groups: {', '.join(row['pul:Ad hoc Groups'].split(','))}"
    entry += f"\n{leading_space}Link: https://library.princeton.edu/staff/{row['netid']}"
    entry += "\n"
    return entry

def format_entry_as_dict(row):
    d = {
        'name' : row['pul:Preferred Name'],
        'title' : row['Title'], 
        'link' : f"https://library.princeton.edu/staff/{row['netid']}"
    }
    if row.get("pul:Team"):
        d['team'] = row['pul:Team']
    elif row.get("pul:Unit"):
        d['unit'] = row['pul:Unit']
    elif row.get("pul:Department"):
        d['department'] = row['pul:Department']
    else:
        d['division'] = row['Division']
    if row.get('pul:Ad hoc Groups'):
        d['groups'] = row['pul:Ad hoc Groups'].split(',')
    return d
        

def list_reports(row, leading_space='', f=stdout, fmt='txt'):
    print(format_entry(row, leading_space=leading_space), file=stdout)
    reports = get_reports(row)
    # recursive case
    if reports:
        leading_space = leading_space + INDENT
        for report in reports:
            list_reports(report, leading_space=leading_space)
    # base case is to do nothing

def list_reports_as_dict(row, d={}):
    entry = format_entry_as_dict(row)
    if len(d) == 0: # i.e. it's empty:
        d = entry
    else:
        d['staff'].append(entry)
    reports = get_reports(row)
    # recursive case
    if reports:
        entry['staff'] = []
        for report in reports:
            list_reports_as_dict(report, entry)
    return d
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
    # list_reports(ROWS[0])# txt 
    org_dict = list_reports_as_dict(ROWS[0]) # report needs AJ on the first line.
    print_json(org_dict)

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



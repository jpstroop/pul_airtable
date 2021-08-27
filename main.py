from json import dumps
from json import load
from requests import get
from time import sleep

API_BASE = 'https://api.airtable.com/v0/'
THROTTLE_INTERVAL = 0.2

def load_private(pth='./private.json'):
    with open(pth, 'r') as f:
        return load(f)

def list_netids(app_path, api_key):
    params = {
        'fields[]': ('netid', 'Name'),
        'filterByFormula': 'NOT(REGEX_MATCH({Name}, "^__"))'
    }
    headers = {'Authorization': f'Bearer {api_key}'}
    url = f'{API_BASE}{app_path}'
    # TODO paging and filtering to exclude __VACANCY_X+__
    r = get(url, params=params, headers=headers)
    # TODO handle non-200 (requests has a method, I think?)
    return r.json()



if __name__ == '__main__':
    private_data = load_private()
    api_key = private_data['AIRTABLE_API_KEY']
    app_path = private_data['APP_PATH']
    netids = list_netids(app_path, api_key)
    print(dumps(netids, ensure_ascii=False, indent=2))
    # get the netid and ids

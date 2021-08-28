from requests import get
from time import sleep

class AirTableAPI():

    API_BASE = 'https://api.airtable.com/v0/'
    THROTTLE_INTERVAL = 0.2

    def __init__(self, app_path, api_key):
        self.app_path = app_path
        self.api_key = api_key

    def list_netids(self):
        params = {
            'fields[]': ('netid', 'Name'),
            'filterByFormula': 'NOT(REGEX_MATCH({Name}, "^__VACANCY_"))'
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}
        url = f'{AirTableAPI.API_BASE}{self.app_path}'
        # TODO paging
        r = get(url, params=params, headers=headers)
        r.raise_for_status()
        # TODO handle non-200s
        return r.json()

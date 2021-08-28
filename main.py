from airtable import AirTableAPI
from json import load
from ldap import LDAP_API
from sys import stderr

def debug_dump(json_payload):
    from json import dumps
    print(dumps(json_payload, ensure_ascii=False, indent=2))

class UpdateApp():
    def __init__(self):
        private = UpdateApp._load_private()
        self.airtable = AirTableAPI(private['APP_PATH'], private['AIRTABLE_API_KEY'])
        self.ldap = LDAP_API(private['LDAP_HOST'], private['LDAP_OC'])

    @staticmethod
    def _load_private(pth='./private.json'):
        with open(pth, 'r') as f:
            return load(f)

    def airtable_patch_data_from_ldap(self, netid, airtable_id):
        ldap_data = self.ldap.query('uid', netid)
        if ldap_data is None:
            raise Exception(f'LDAP entry not found for {netid}')
        return {
            'records' : [
                {
                    'id': airtable_id,
                    'fields': {
                        'Name': ldap_data.get('displayName'),
                        'First Name': ldap_data.get('givenName'),
                        'Last Name': ldap_data.get('sn'),
                        'University ID': ldap_data.get('universityid'),
                        'Email': ldap_data.get('mail'),
                        'University Phone': ldap_data.get('telephoneNumber'),
                        'Address': ldap_data.get('street')
                    }
                }
            ]
        }

if __name__ == '__main__':

    app = UpdateApp()


    # netids = app.airtable.list_netids()
    # for record in netids['records']:
    #     id = record['id']
    #     netid = record['fields']['netid']
    #     patch_body = app.airtable_patch_data_from_ldap(netid, id)
    #     try:
    #         app.airtable.patch_record(patch_body)
    #     except Exception as e:
    #         print(f'Error for {netid}')
    #         print(e.message, file=stderr)
    #         continue

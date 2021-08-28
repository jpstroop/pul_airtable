from json import load
from ldap import LDAP_API
from airtable import AirTableAPI

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
        return {
            'records' : [
                {
                    'id': airtable_id,
                    'fields': {
                        'Name': ldap_data.get('displayName'),
                        'First Name': ldap_data.get('givenName'),
                        'Last Name': ldap_data.get('sn'),
                        'University ID': int(ldap_data.get('universityid')),
                        'Email': ldap_data.get('mail'),
                        'University Phone': ldap_data.get('telephoneNumber'),
                        'Address': ldap_data.get('street')
                    }
                }
            ]
        }


    # TODO: we want:


if __name__ == '__main__':
    app = UpdateApp()
    # get all netids and ids
    # netids = app.airtable.list_netids()

    # for each, reformat and patch
    patch_body = app.airtable_patch_data_from_ldap('kl37', 'reciI0wlyLxnEi3GZ')
    debug_dump(patch_body)
    app.airtable.patch_record(patch_body)


    # app.airtable_patch_data_from_ldap('fkayiwa')

    #
    # netids = airtable.list_netids()
    # debug_dump(netids)


    # ldap
    # data = ldap.query('uid', 'kayiwa')
    # print(dumps(data, ensure_ascii=False, indent=2))

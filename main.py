from json import dumps
from json import load
from ldap import LDAP_API
from airtable import AirTableAPI

def load_private(pth='./private.json'):
    with open(pth, 'r') as f:
        return load(f)




if __name__ == '__main__':
    private_data = load_private()
    api_key = private_data['AIRTABLE_API_KEY']
    app_path = private_data['APP_PATH']
    ldap_host = private_data['LDAP_HOST']
    ldap_oc = private_data['LDAP_OC']

    # airtable = AirTableAPI(app_path, api_key)
    # netids = airtable.list_netids()
    # print(dumps(netids, ensure_ascii=False, indent=2))


    ldap = LDAP_API(ldap_host, ldap_oc)
    data = ldap.query('uid', 'kayiwa')
    print(dumps(data, ensure_ascii=False, indent=2))
    # TODO: we want:
    # First Name (givenName)
    # Last Name (sn)
    # netid (should be uid)
    # Univeristy ID (universityid)
    # Email (mail)
    # University Phone (telephoneNumber)
    # Address (street)
